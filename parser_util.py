import cv2
import numpy as np
import math
from configuration.configuration import ScannerConfiguration


def vector_normal(p1, p2, p3):
    v1 = [(p1[0]-p2[0]), (p1[1]-p2[1]), (p1[2]-p2[2])]
    v2 = [(p3[0]-p2[0]), (p3[1]-p2[1]), (p3[2]-p2[2])]
    #v1, v2 = vector_angle(v1, v2, offset)
    n = [(v1[1]*v2[2]-v1[2]*v2[1]), -1*(v1[0]*v2[2]-v1[2]*v2[0]), (v1[0]*v2[1]-v1[1]*v2[0])]
    if p2[9]:
        n = [n[0]*-1, n[1]*-1, n[2]*-1]
    v1m = math.sqrt(math.pow(v1[0], 2) + math.pow(v1[1], 2) + math.pow(v1[2], 2))
    v2m = math.sqrt(math.pow(v2[0], 2) + math.pow(v2[1], 2) + math.pow(v2[2], 2))
    vm = v1m * v2m
    if vm == 0:
        return [0.0, 0.0, 0.0]
    else:
        return [n[0]/vm, n[1]/vm, n[2]/vm]


def calculate_normal_vector(xyz, xyz2, flip=False):
    length = len(xyz)
    l2 = len(xyz2)
    if l2 <= 1:
        return xyz
    r = 8
    for i in range(0, length-r, 1):
        if flip:
            p1 = xyz2[i if i < l2 else l2-1]
        else:
            p1 = xyz[i]
        p2 = xyz[i+r]
        if flip:
            p3 = xyz[i]
        else:
            p3 = xyz2[i if i < l2 else l2-1]
        n = vector_normal(p2, p1, p3)

        xyz[i][6] = n[0]
        xyz[i][7] = n[1]
        xyz[i][8] = n[2]
    return xyz


def points_triangulate(config: ScannerConfiguration, points, offset, color=None, right=True):
    left_offset = 0
    if right:
        cam_degree = config.right_laser.angle
        #cam_degree = 30.0
    else:
        cam_degree = -config.left_laser.angle
        #cam_degree = -30.0
        left_offset = 0.0
        #left_offset = -(config.right_laser.angle + config.left_laser.angle)

    px, py = points

    bgr = [147, 201, 3]
    if color is not None and right:
        bgr = [0, 0, 255]
        #bgr = color[round(py), round(px)]

    cx = config.camera.cx-2.5
    cy = config.camera.cy
    #calc_x = (float(px)-cx)/config.camera.f + 0.75 if right else (cx - float(px))/config.camera.f - 0.75
    calc_x = (float(px)-cx)/config.camera.f
    flip = calc_x < 0.0
    """
    if right:
        calc_x = (float(px)-cx)/config.camera.f
        flip = calc_x < 0.0
    else:
        calc_x = (cx-float(px))/config.camera.f
        flip = calc_x > 0.0

    if right:
        calc_z = -calc_x / math.tan(math.radians(cam_degree))
    else:
        calc_z = calc_x / math.tan(math.radians(cam_degree))
    """
    calc_z = -calc_x / math.tan(math.radians(cam_degree))
    #a =  / config.camera.f
    f = config.camera.new_camera_mtx[1][1]/(355.65 + calc_z)
    calc_y = (float(py)-cy) / f

    if not right:
        offset += left_offset
    angle = math.radians(offset)

    orig_x = calc_x
    orig_z = calc_z
    calc_x = orig_x*math.cos(angle) - orig_z*math.sin(angle)
    calc_z = orig_x*math.sin(angle) + orig_z*math.cos(angle)

    return [
        calc_x,
        calc_y,
        calc_z,
        bgr[2], bgr[1], bgr[0],
        0.0, 0.0, 0.0, flip
    ]


def points_max_cols(img, threshold=(60, 255), c=False, roi=None, right=True):

    lower = np.array([30, 20, 60])
    upper = np.array([175, 125, 255])
    if c:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        t_min, t_max = threshold
        ret, bin_img = cv2.threshold(gray, t_min, t_max, cv2.THRESH_BINARY)
        # contour, hierarchy = cv2.findContours(bin_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        h, w = bin_img.shape
        c = cv2.resize(bin_img, (360, 640), interpolation=cv2.INTER_AREA)
        #cv2.imshow("pic", c)
        #cv2.waitKey()
        #cv2.destroyAllWindows()
    else:
        bin_img = cv2.inRange(img, lower, upper)
        h, w, _ = img.shape

    """
    if roi is None:
        x_roi, y_roi = get_roi_by_img(img, 1)
    else:
    """
    x_roi = roi[0]
    y_roi = roi[1]

    s = 1
    if right:
        s = -1
        x_roi = [x_roi[1]-1, x_roi[0]-1]

    xy = list()

    avg = []
    for i in range(0, h):
        avg.append([0, 0])

    for y in range(y_roi[0], y_roi[1], 4):
        found = False
        for x in range(x_roi[0], x_roi[1], s):
            if bin_img[y][x] > 0:
                avg[y][0] += x
                avg[y][1] += 1
                found = True
            else:
                if found:
                    break

    for i in range(0, len(avg)):
        a = avg[i]
        if a[1] > 0:
            x_avg = int(round(a[0]/a[1], 0))
            xy.append((x_avg, i))

    return xy