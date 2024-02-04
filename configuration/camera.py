import os.path
import pickle
import numpy as np
import cv2
import glob
import accessories.camera as camera
import time

from accessories.stepper_motor import StepperMotor
from scanner_paths import calibration_path

pickle_file = 'configuration.p'

grid_size = 14.7
nx = 6              # nx: number of grids in x-axis
ny = 9              # ny: number of grids in y-axis

objp = np.zeros((nx * ny, 3), np.float32)
objp[:, :2] = np.mgrid[0:nx, 0:ny].T.reshape(-1, 2)
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

out = True
printed = False


class CameraConfiguration(object):
    def __init__(self, calculate=False):
        self.rx = 0.0
        self.ry = 0.0
        self.r = 0.0
        self.f = 0.0
        self.f_mm = 0.0
        self.cx = 0.0
        self.cy = 0.0
        self.cz = 0.0
        self.grid_size = grid_size
        self.nx = nx
        self.ny = ny
        self.mtx = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        self.dist = []

    def correct_distortion(self, img, crop=True):
        h, w = img.shape[:2]

        new_camera_mtx, roi = cv2.getOptimalNewCameraMatrix(self.mtx, self.dist, (w, h), 1, (w, h))
        undistorted_img = cv2.undistort(img, self.mtx, self.dist, None, new_camera_mtx)

        if crop:
            x, y, w, h = roi
            undistorted_img = undistorted_img[y:y + h, x:x + w]
        return undistorted_img

    def correct_distortion_file(self, img_path, crop=True):
        img = cv2.imread(img_path)
        return self.correct_distortion(img, crop)

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

            h, w = img.shape[:2]
            if h < w:
                img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                h, w = img.shape[:2]

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

        if gray_pic is None:
            raise Exception('Calibration failed. Chessboard corners could not be found in any image.')

        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(obj_points, img_points, gray_pic.shape[::-1], None, None)
        new_camera_mtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))

        print('calibrationMatrixValues-mtx', cv2.calibrationMatrixValues(mtx, gray_pic.shape[::-1], 6.4512, 3.6288))
        print('calibrationMatrixValues-new_cam', cv2.calibrationMatrixValues(new_camera_mtx, gray_pic.shape[::-1], 6.4512, 3.6288))
        print(mtx, new_camera_mtx)
        fov_x, fov_y, f, pp, ar = cv2.calibrationMatrixValues(new_camera_mtx, gray_pic.shape[::-1], 6.4512, 3.6288)
        r_diff = 100.0
        for f_name in images:
            img = cv2.imread(f_name)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Should we correct distortion??
            # gray = cv2.undistort(gray, mtx, dist, None, new_camera_mtx)

            # Find the chess board corners
            ret, corners = cv2.findChessboardCorners(gray, (nx, ny), None)
            if ret:
                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                px = corners2[(ny - 1) * nx][0][0]
                pdx = 0
                pdy = 0
                pdt = 0

                x_a = []
                # print(configuration.corners_ret)
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
                    self.rx = round(pdx, 2)
                    self.ry = round(pdy, 2)
                print('corners', i, px, pdx, pdy)

        if mtx is not None or dist is not None:
            """
            self._config['f'] = round((new_camera_mtx[0][0] + new_camera_mtx[1][1])/2.0, 2)
            self._config['cx'] = round(new_camera_mtx[0][2], 2)
            self._config['cy'] = round(new_camera_mtx[1][2], 2)
            """
            self.f = round((mtx[0][0] + mtx[1][1])/2.0, 2)
            self.f_mm = f
            self.r = round(grid_size * f, 1)
            self.cx = round(mtx[0][2], 2)
            self.cy = round(mtx[1][2], 2)
            self.cz = round(self.f / f, 1)
            self.mtx = mtx
            self.dist = dist
            self.save_calibration()
            return True
        return False

    def save_calibration(self):
        source = os.path.join(calibration_path, pickle_file)
        pickle.dump(self, open(source, "wb"))

    def run_calibration(self, motor: StepperMotor):
        motor.enable()
        steps = 30
        degrees = 2.5
        motor.rotate(35, True)
        time.sleep(0.8)
        camera.set_config('save')
        for i in range(0, steps):
            if i > 0:
                motor.rotate(degrees, False)

            try:
                camera.capture_file_cam(f'%s/calibration_%04d.jpg' % (calibration_path, i))
                print('captured', f'%s/calibration_%04d.jpg' % (calibration_path, i))
            except:
                print('error taking photo')
                pass
            time.sleep(0.8)

        motor.rotate(37.5, True)
        motor.disable()
        ret = self.determine_calibration()
        if not ret:
            print('configuration failed.')

