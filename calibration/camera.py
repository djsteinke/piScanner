import os.path
import pickle
import numpy as np
import cv2
import glob
from os import path
import accessories.camera as camera
import time

from accessories.stepper_motor import StepperMotor
from scanner_paths import calibration_path

pickle_file = 'calibration.p'

grid_size = 14.7
nx = 9              # nx: number of grids in x axis
ny = 6              # ny: number of grids in y axis

objp = np.zeros((nx * ny, 3), np.float32)
objp[:, :2] = np.mgrid[0:nx, 0:ny].T.reshape(-1, 2)
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

out = True
printed = False


class CameraCalibration(object):
    def __init__(self, calculate=False):
        self._config = {
            "rx": 0.0,
            "ry": 0.0,
            "f": 0.0,
            "cx": 0.0,
            "cy": 0.0,
            "cz": 0.0,
            "mtx": None,
            "dist": None
        }
        if calculate:
            self.load_calibration(calculate)

    def undistort_img(self, img, crop=True):
        h, w = img.shape[:2]
        if h < w:
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            h, w = img.shape[:2]
        new_camera_mtx, roi = cv2.getOptimalNewCameraMatrix(self._config['mtx'], self._config['dist'], (w, h), 1, (w, h))
        undistorted_img = cv2.undistort(img, self._config['mtx'], self._config['dist'], None, new_camera_mtx)

        if crop:
            x, y, w, h = roi
            undistorted_img = undistorted_img[y:y + h, x:x + w]
        # img_color = cv2.cvtColor(img_undist, cv2.COLOR_GRAY2RGB)
        return undistorted_img

    def undistort_file(self, img_path, crop=True):
        img = cv2.imread(img_path)
        return self.undistort_img(img, crop)

    def determine_calibration(self):
        obj_points = []  # 3d point in real world space
        img_points = []  # 2d points in image plane.

        p = calibration_path

        images = glob.glob('%s/calibration_*.jpg' % p.rstrip('/'))
        print(len(images))

        gray_pic = None
        i = 0
        h, w = 0, 0
        for f_name in images:
            img = cv2.imread(f_name)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            if gray_pic is None:
                gray_pic = gray
            # Find the chess board corners
            ret, corners = cv2.findChessboardCorners(gray, (nx, ny), None)

            # print(f_name, "found chessboard", ret)
            if ret:
                if h == 0:
                    h, w = img.shape[:2]
                obj_points.append(objp)

                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                img_points.append(corners2)

                # Draw and display the corners
                # img = cv2.drawChessboardCorners(img, (nx, ny), corners2, ret)
                # cv2.imshow('img', img)
                # cv2.waitKey(500)

        if gray_pic is None:
            return None, None

        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(obj_points, img_points, gray_pic.shape[::-1], None, None)
        new_camera_mtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (h, w), 1, (h, w))

        print('calibrationMatrixValues-mtx', cv2.calibrationMatrixValues(mtx, gray_pic.shape[::-1], 6.4512, 3.6288))
        print('calibrationMatrixValues-new_cam', cv2.calibrationMatrixValues(new_camera_mtx, gray_pic.shape[::-1], 6.4512, 3.6288))
        print(mtx, new_camera_mtx)
        fov_x, fov_y, f, pp, ar = cv2.calibrationMatrixValues(new_camera_mtx, gray_pic.shape[::-1], 6.4512, 3.6288)
        gray_pic = None
        r_diff = 100.0
        for f_name in images:
            img = cv2.imread(f_name)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.undistort(gray, mtx, dist, None, new_camera_mtx)

            #x, y, w, h = roi
            #gray = gray[y:y + h, x:x + w]
            #print(gray.shape)

            # Find the chess board corners
            ret, corners = cv2.findChessboardCorners(gray, (nx, ny), None)
            if ret:
                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                px = corners2[(ny - 1) * nx][0][0]
                pdx = 0
                pdy = 0
                pdt = 0

                x_a = []
                # print(calibration.corners_ret)
                for y in range(0, ny - 1):
                    for x in range(0, nx - 1):
                        pdt += 1
                        p = y * nx + x
                        pdx += abs(corners2[p + 1][0][0] - corners2[p][0][0])
                        pdy += abs(corners2[p + nx][0][1] - corners2[p][0][1])
                pdx /= pdt
                pdy /= pdt
                x_a.append(pdx)
                i += 1
                # Rx, Ry, f, Cx, Cy, Cz
                if abs(pdx-pdy) < r_diff:
                    r_diff = abs(pdx-pdy)
                    self._config['rx'] = round(pdx, 2)
                    self._config['ry'] = round(pdy, 2)
                print('corners', i, px, pdx, pdy)

        # cv2.destroyAllWindows()

        if mtx is not None or dist is not None:
            self._config['f'] = round((new_camera_mtx[0][0] + new_camera_mtx[1][1])/2.0, 2)
            self._config['cx'] = round(new_camera_mtx[0][2], 2)
            self._config['cy'] = round(new_camera_mtx[1][2], 2)
            self._config['cz'] = round(grid_size * f, 1)
            self._config['mtx'] = mtx
            self._config['dist'] = dist
            print('config', self._config)
            self.save_calibration()
            return True
        return False

    def load_calibration(self, calculate):
        source = os.path.join(calibration_path, pickle_file)
        if calculate:
            ret = self.determine_calibration()
            if not ret:
                print('calibration failed.')
        else:
            with open(source, 'rb') as file:
                data = pickle.load(file)
                self._config = {
                    "rx": data['rx'],
                    "ry": data['ry'],
                    "f": data['f'],
                    "cx": data['cx'],
                    "cy": data['cy'],
                    "cz": data['cz'],
                    "mtx": data['mtx'],
                    "dist": data['dist']
                }

    def save_calibration(self):
        source = os.path.join(calibration_path, pickle_file)
        pickle.dump(self._config, open(source, "wb"))

    @property
    def mtx(self):
        if self._config['mtx'] is None:
            return [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        else:
            return self._config['mtx']


def run_calibration(motor: StepperMotor):
    steps = 10
    degrees = 5.0
    images_path = path.join(calibration_path, 'images')
    motor.rotate(25, True)
    time.sleep(0.5)
    camera.set_config('save')
    for i in range(1, steps):
        try:
            camera.capture_file_cam(f'%s/calibration_%04d.jpg' % (calibration_path, i))
            print('captured', f'%s/calibration_%04d.jpg' % (calibration_path, i))
        except:
            print('error taking photo')
            pass
        motor.rotate(degrees, False)
        time.sleep(0.5)

    motor.rotate(25, True)

    CameraCalibration(True)

"""
p = getcwd() + "\\calibration\\android"
print(p)
if path.isfile(p + "\\calibration_0001.jpg"):
    print("cal exists")
else:
    print("incorrect path")
cal = CameraCalibration(wd=p, reload=True)
print(cal.mtx)
print(cal.config)
"""
# f 1536.5 / Cx 534 / Cy 962 / f 8.02 / 73.4 / Cz 303.4
# f 1520.7 / Cx 571.5 / Cy 945.0 / f 7.94