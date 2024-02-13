import os
import cv2
import math
from configuration.configuration import ScannerConfiguration


def correct_images():
    cwd = os.getcwd()
    cwd = os.path.join(cwd, 'scans')
    cwd = os.path.join(cwd, '20240210112234')
    imgd = os.path.join(cwd, 'images')
    imgd_r = os.path.join(imgd, 'right_0000.jpg')
    imgd_l = os.path.join(imgd, 'left_0000.jpg')
    imgs_r = os.path.join(cwd, 'right.jpg')
    imgs_l = os.path.join(cwd, 'left.jpg')
    img_r = cv2.imread(imgd_r)
    img_r = config.camera.correct_distortion(img_r)
    cv2.imwrite(imgs_r, img_r)
    img_l = cv2.imread(imgd_l)
    img_l = config.camera.correct_distortion(img_l)
    cv2.imwrite(imgs_l, img_l)


def get_x_y_z(ps, right):
    for p in ps:
        cam_degree = 30 if right else -30
        x = (float(p[0]) - config.camera.new_camera_mtx[0][2])/config.camera.f
        dz = - config.camera.new_camera_mtx[0][0] * x / (float(p[0]) - config.camera.new_camera_mtx[0][2])
        y = (float(p[1]) - config.camera.new_camera_mtx[1][2]) / config.camera.f
        z = x / math.tan(math.radians(cam_degree))
        print(x, y, z, dz)


if __name__ == "__main__":
    config = ScannerConfiguration.load()
    print(config.camera.f)
    print(config.camera.new_camera_mtx)
    p_r = [[689, 711],
           [617, 1111],
           [782, 1662]]
    p_l = [[476, 892],
           [472, 1259],
           [269, 1662]]
    get_x_y_z(p_r, True)
    get_x_y_z(p_l, False)
    # correct_images()
