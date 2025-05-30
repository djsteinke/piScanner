import numpy as np
import cv2
import glob
import accessories.camera as camera
import time

from scanner_paths import calibration_images_path

criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

out = True
printed = False


def arrary_avg(arr):
    i = 0
    x = 0
    y = 0
    z = 0
    for a in arr:
        i += 1
        x += a[0]
        y += a[1]
        z += a[2]
    x /= i
    y /= i
    z /= i
    print(np.array([[x], [y], [z]], dtype=np.float32))

class CameraConfiguration(object):
    def __init__(self, calculate=False):
        #self.rx: float = 0.0
        #self.ry: float = 0.0
        #self.r: float = 0.0
        #self.f: float = 0.0
        self.fx: float = 0.0
        self.fy: float = 0.0
        self.f: float = 0.0
        self.cx: float = 0.0
        self.cy: float = 0.0
        self.cz: int = 0
        self.grid_size: float = 15
        self.nx: int = 6
        self.ny: int = 9
        self.mtx = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        self.dist = []
        self.new_camera_mtx = []
        self.roi = []

    def calibration_values(self):
        return {
            "fx": self.fx,
            "fy": self.fy,
            "f": self.f,
            "cx": self.cx,
            "cy": self.cy,
            "cz": self.cz
        }

    def correct_distortion(self, img, crop=False, mtx=None, dist=None, new_camera_mtx=None):
        if mtx is None or dist is None or new_camera_mtx is None:
            mtx = self.mtx
            dist = self.dist
            new_camera_mtx = self.new_camera_mtx

        h, w = img.shape[:2]
        if h < w:
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            h, w = img.shape[:2]
        undistorted_img = cv2.undistort(img, mtx, dist, None, new_camera_mtx)
        if crop and len(self.roi) == 4:
            x, y, w, h = self.roi
            undistorted_img = undistorted_img[y:y + h, x:x + w]
        return undistorted_img

    def correct_crop_file(self, img_path, crop=True):
        img = cv2.imread(img_path)
        return self.correct_distortion(img, crop)

    def take_correct_pic(self, file_name):
        path = f'%s/%s.jpg' % (calibration_images_path, file_name)
        camera.capture_file_cam(f'%s/%s.jpg' % (calibration_images_path, file_name))
        img = self.correct_crop_file(path, False)
        cv2.imwrite(path, img)

    def determine_calibration(self):
        obj_points = []  # 3d point in real world space
        img_points = []  # 2d points in image plane.
        nx = self.nx
        ny = self.ny
        print(nx, ny)
        objp = np.zeros((nx * ny, 3), np.float32)
        objp[:, :2] = np.mgrid[0:nx, 0:ny].T.reshape(-1, 2)

        p = calibration_images_path

        images = glob.glob('%s/calibration_*.jpg' % p.rstrip('/'))
        print(len(images))

        gray_pic = None
        h, w, rx, ry = 0, 0, 0.0, 0.0
        for f_name in images:
            img = cv2.imread(f_name)
            h, w = img.shape[:2]
            if h < w:
                img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                h, w = img.shape[:2]

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            ret, corners = cv2.findChessboardCorners(gray, (nx, ny), None)

            if ret:
                obj_points.append(objp)

                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                img_points.append(corners2)
                if gray_pic is None:
                    gray_pic = gray
            print(f_name, "found chessboard", ret, h, w)
        if gray_pic is None:
            raise Exception('Calibration failed. Chessboard corners could not be found in any image.')

        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(obj_points, img_points, gray_pic.shape[::-1], None, None)
        new_camera_mtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))

        arrary_avg(rvecs)
        arrary_avg(tvecs)
        print('calibrationMatrixValues-mtx', cv2.calibrationMatrixValues(mtx, gray_pic.shape[::-1], 3.6288, 6.4512))
        print('calibrationMatrixValues-new_cam', cv2.calibrationMatrixValues(new_camera_mtx, gray_pic.shape[::-1], 3.6288, 6.4512))
        fov_x, fov_y, f, pp, ar = cv2.calibrationMatrixValues(new_camera_mtx, gray_pic.shape[::-1], 3.6288, 6.4512)
        print(mtx)
        print(w, h, new_camera_mtx, roi)

        correct = self.correct_distortion(gray_pic, mtx=mtx, dist=dist, new_camera_mtx=new_camera_mtx)
        cv2.imwrite('corrected.jpg', correct)
        """
        c_img = cv2.line(orig_pic, (round(mtx[0][2]), 0), (round(mtx[0][2]), h), (0, 0, 255), 2)
        c_img = cv2.line(c_img, (0, round(mtx[1][2])), (w, round(mtx[1][2])), (0, 0, 255), 2)
        c_img = self.correct_distortion(c_img, False)
        c_img = cv2.line(c_img, (round(new_camera_mtx[0][2]), 0), (round(new_camera_mtx[0][2]), h), (0, 255, 0), 1)
        c_img = cv2.line(c_img, (0, round(new_camera_mtx[1][2])), (w, round(new_camera_mtx[1][2])), (0, 255, 0), 1)
        cv2.imwrite('corrected.jpg', c_img)
        cv2.imwrite('corrected_crop.jpg', self.correct_distortion(gray_pic))
        print('calibrationMatrixValues-mtx', cv2.calibrationMatrixValues(mtx, gray_pic.shape[::-1], 3.6288, 6.4512))
        print('calibrationMatrixValues-new_cam', cv2.calibrationMatrixValues(new_camera_mtx, gray_pic.shape[::-1], 3.6288, 6.4512))
        print(mtx)
        print(roi, new_camera_mtx)
        # fov_x, fov_y, f, pp, ar = cv2.calibrationMatrixValues(new_camera_mtx, gray_pic.shape[::-1], 6.4512, 3.6288)
        fov_x, fov_y, f, pp, ar = cv2.calibrationMatrixValues(mtx, gray_pic.shape[::-1], 3.6288, 6.4512)
        r_diff = 100.0
        r_x, r_y, r_w, r_h = roi
        for f_name in images:
            img = cv2.imread(f_name)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Should we correct distortion??
            gray = cv2.undistort(gray, mtx, dist, None, new_camera_mtx)
            gray = gray[r_y:r_y + r_h, r_x:r_x + r_w]

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
                    print('new rx ry', pdx, pdy)
        """

        if mtx is not None or dist is not None and new_camera_mtx is not None:
            self.fx = round(new_camera_mtx[0][0], 2)
            self.fy = round(new_camera_mtx[1][1], 2)
            self.f = round(f, 3)
            self.cx = round(new_camera_mtx[0][2], 2)
            self.cy = round(new_camera_mtx[1][2], 2)

            self.mtx = mtx
            self.dist = dist
            self.new_camera_mtx = new_camera_mtx
            self.roi = roi
            return True
        return False

    def run_calibration(self, motor):
        motor.enable()
        steps = 19
        degrees = 5
        motor.rotate(45, True)
        time.sleep(0.8)
        camera.set_config('save')
        for i in range(0, steps):
            if i > 0:
                motor.rotate(degrees, False)

            try:
                camera.capture_file_cam(f'%s/calibration_%04d.jpg' % (calibration_images_path, i))
                print('captured', f'%s/calibration_%04d.jpg' % (calibration_images_path, i))
            except:
                print('error taking photo')
                pass
            time.sleep(0.8)

        motor.rotate(45, True)
        motor.disable()
        ret = self.determine_calibration()
        if not ret:
            print('configuration failed.')

    """
    def determine_c_z(self):
        print(self.calibration_values())
        motor.enable()
        camera.capture_file_cam(f'%s/cz_01.jpg' % calibration_path)
        print('pic 1 captured')
        motor.rotate(45, False)
        time.sleep(1)
        print('rotated')
        camera.capture_file_cam(f'%s/cz_02.jpg' % calibration_path)
        print('pic 2 captured')
        motor.rotate(45, True)

        motor.rotate(45, True)

        img = cv2.imread(f'%s/cz_01.jpg' % calibration_path)
        h, w = img.shape[:2]
        if h < w:
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        new_camera_mtx, roi = cv2.getOptimalNewCameraMatrix(self.mtx, self.dist, (w, h), 1, (w, h))
        gray = cv2.undistort(gray, self.mtx, self.dist, None, new_camera_mtx)
        ret, corners = cv2.findChessboardCorners(gray, (self.nx, self.ny), None)
        corners2 = corners
        if ret:
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            pdy = 0
            pdx = 0
            pdt = 0
            for y in range(0, self.ny - 1):
                for x in range(0, self.nx - 1):
                    pdt += 1
                    p = y * self.nx + x
                    pdx += abs(corners2[p + 1][0][0] - corners2[p][0][0])
                    pdy += abs(corners2[p + self.nx][0][1] - corners2[p][0][1])
            pdx /= pdt
            pdy /= pdt
            print('corners undistort crop', pdt, pdx, pdy)
            self.rx = pdx
            self.ry = pdy

        p = (self.nx - 1) * (self.ny - 1) - 1
        p1 = corners2[p][0]
        print('p1', p1)

        img = cv2.imread(f'%s/cz_02.jpg' % calibration_path)
        h, w = img.shape[:2]
        if h < w:
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.undistort(gray, self.mtx, self.dist, None, new_camera_mtx)
        ret, corners = cv2.findChessboardCorners(gray, (self.nx, self.ny), None)
        corners2 = corners
        if ret:
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        p2 = corners2[p][0]

        print('p2', p2)
        X1 = (p1[0]-self.cx)/self.rx*self.grid_size
        Z2 = X1*math.sin(math.radians(45))
        cz = Z2 * (self.cy - p2[1]) / (p2[1] - p1[1])
        print(cz)
    """

    def calibrate_single_shot(self, file_name, started=False, pic=False):
        if pic and not started:
            camera.camera.start()
            camera.camera.set_focus_mm(350.0)
        if pic:
            camera.capture_file_cam(f'%s/%s.jpg' % (calibration_images_path, file_name))

        img = cv2.imread(f'%s/%s.jpg' % (calibration_images_path, file_name))
        h, w = img.shape[:2]
        if h < w:
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            h, w = img.shape[:2]
        # print(w, h, self.mtx)
        new_camera_mtx, roi = cv2.getOptimalNewCameraMatrix(self.mtx, self.dist, (w, h), 1, (w, h))
        img = cv2.undistort(img, self.mtx, self.dist, None, new_camera_mtx)
        # print('calibrationMatrixValues-new_cam', cv2.calibrationMatrixValues(new_camera_mtx, img.shape[:2], 3.6288, 6.4512))
        x, y, w, h = roi
        # gray = gray[y:y + h, x:x + w]
        # print(x, y, w, h, new_camera_mtx)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, (self.nx, self.ny), None)
        if ret:
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            print(corners2[0], corners2[self.nx * self.ny - 1], corners2[self.nx-1], corners2[self.nx * self.ny - self.nx])
            img = cv2.drawChessboardCorners(img, (self.nx, self.ny), corners2, ret)
            cv2.imwrite(file_name + '_corr.jpg', img)
            pdx = 0
            pdy = 0
            pdy_x = 0
            pdx_x = 0
            pdx_y = 0
            pdy_y = 0
            pdt = 0
            pdt_y = 0
            for y in range(0, self.ny - 1):
                pdt_x = 0
                pdt_y += 1
                for x in range(0, self.nx - 1):
                    pdt += 1
                    pdt_x += 1
                    p = y * self.nx + x
                    pdx += abs(corners2[p + 1][0][0] - corners2[p][0][0])
                    pdy += abs(corners2[p + self.nx][0][1] - corners2[p][0][1])
                    pdx_x += abs(corners2[p + 1][0][0] - corners2[p][0][0])
                    pdy_x += abs(corners2[p + self.nx][0][1] - corners2[p][0][1])

                p = y * self.nx
                pdy_y += abs(corners2[p + 1][0][1] - corners2[p][0][1])
                pdx_y += abs(corners2[p + self.nx][0][0] - corners2[p][0][0])
                pdx_x /= pdt_x
                pdy_x /= pdt_x
                pdx_y /= pdt_y
                pdy_y /= pdt_y
                print('pts', pdt_x, pdx_x, pdy_x, pdt_y, pdx_y, pdy_y)
            pdx /= pdt
            pdy /= pdt
            print('corners undistort crop', pdt, pdx, pdy)
            print('cz', round(new_camera_mtx[0][0]/(pdx/self.grid_size), 2), round(new_camera_mtx[1][1]/(pdy/self.grid_size), 2))

        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, (self.nx, self.ny), None)
        if ret:
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            pdy = 0
            pdx = 0
            pdt = 0
            for y in range(0, self.ny - 1):
                for x in range(0, self.nx - 1):
                    pdt += 1
                    p = y * self.nx + x
                    # print(abs(corners2[p + 1][0][0] - corners2[p][0][0]), abs(corners2[p + nx][0][1] - corners2[p][0][1]))
                    pdx += abs(corners2[p + 1][0][0] - corners2[p][0][0])
                    pdy += abs(corners2[p + self.nx][0][1] - corners2[p][0][1])
            pdx /= pdt
            pdy /= pdt
            print('corners', pdt, pdx, pdy)
            print('cz', round(self.mtx[0][0]/(pdx/self.grid_size), 2), round(self.mtx[1][1]/(pdy/self.grid_size), 2))
        """