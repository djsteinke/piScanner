import argparse
import os.path
import glob
import cv2

import scanner_paths
from scan import ScanDetails
from configuration.configuration import ScannerConfiguration
from parser_util import *

def output_asc_pointset(filename, points, pointset_type='xyz'):
    """
    Write pointset to disk in raw ASCII format .asc

    argument filename File to write
    argument points A 2D array of points [[X,Y,Z,R,G,B]]

    """
    try:
        if pointset_type == 'xyz':
            points = ["%0.2f %0.2f %0.2f" % (x, y, z) for x, y, z, r, g, b in points]
        if pointset_type == 'xyzrgb' or pointset_type == 'xyzn':
            points = ["%0.2f %0.2f %0.2f %0.2f %0.2f %0.2f" % (x, y, z, r, g, b) for x, y, z, r, g, b in points]
        if pointset_type == 'xyzrgb' or pointset_type == 'xyzcn':
            points = ["%0.2f %0.2f %0.2f %d %d %d %0.2f %0.2f %0.2f" % (x, y, z, r, g, b, xn, yn, zn) for x, y, z, r, g, b, xn, yn, zn in points]
    except Exception:
        print(points)
    #points = ["%0.2f %0.2f %0.2f" % (x, y, z) for x, y, z in points]
    points = str.join("\n", points)

    out = open(filename, "w")
    out.write(points)
    out.close()


class ScanParser(object):
    def __init__(self, path):
        self.path = os.path.join(scanner_paths.scans_path, path)
        self.last_xyz = []
        self.first_xyz = []
        self.details = None
        self.config = ScannerConfiguration.load()
        self.load_details()

    def load_details(self):
        try:
            self.details = ScanDetails.load(self.path)
        except:
            raise Exception()

    def validate_path(self):
        if os.path.exists(self.path):
            print(f'parsing {self.path}')
        else:
            print(f'No scan found at {self.path}')
            raise Exception()

    def parse(self):
        image_path = os.path.join(self.path, 'images')
        points = []
        right = glob.glob("%s/right*" % image_path.rstrip('/'))
        left = glob.glob("%s/left*" % image_path.rstrip('/'))
        color = glob.glob("%s/color*" % image_path.rstrip('/'))

        print(f'RIGHT[{len(right)}] LEFT[{len(left)}] COLOR[{len(color)}]')
        if len(color) == 0:
            color = None
        else:
            color.sort()

        if len(right) > 0:
            right.sort()
            points = self.points_process_images(right, color=color, right=True)

        if len(left) > 0:
            left.sort()
            left = self.points_process_images(left, color=color, right=False)
            points.extend(left)

        # draw x, z axis
        """
        xyz = [[x, 0, 0, 255, 0, 0, 0, 0, 0] for x in range(0, 100, 5)]
        points.extend(xyz)
        xyz = [[0, 0, z, 0, 255, 0, 0, 0, 0] for z in range(0, 100, 10)]
        points.extend(xyz)
        """

        filename = os.path.join(self.path, 'points.xyz')
        print("I: Writing pointcloud to %s" % filename)
        output_asc_pointset(filename, points, 'xyzcn')

    def points_process_images(self, images, color=None, right=True):
        points = []
        # images = images[1:]
        s = len(images)
        xyz_all = []
        for i, i_path in enumerate(images):
            if i <= s:
                if right:
                    pic_num = i_path.split('right_')
                else:
                    pic_num = i_path.split('left_')
                pic_num = int(pic_num[1].split('.')[0])
                side = "RIGHT" if right else "LEFT"
                img = cv2.imread(i_path, 0)
                img_c = cv2.imread(i_path)
                c = None
                max_cols_c = True
                if color is not None and i < len(color):
                    # max_cols_c = False
                    c = cv2.imread(color[i])
                    c_gray = cv2.imread(color[i], 0)
                    img = cv2.subtract(img, c_gray)

                h, w = img.shape
                """
                # if we want to resize the images to parse quicker
                if ratio > 1:
                    h_tmp = int(h / ratio)
                    w_tmp = int(w / ratio)
                    img = cv2.resize(img, (w_tmp, h_tmp), interpolation=cv2.INTER_AREA)
                    c = cv2.resize(c, (w_tmp, h_tmp), interpolation=cv2.INTER_AREA)
                    h, w = img.shape
                """
                roi = [[0, 1080], [0, 1920]]
                xy = points_max_cols(img_c, threshold=(60, 255), c=max_cols_c, roi=roi, right=right)
                # xy = remove_noise(xy, w)

                offset = pic_num * float(self.details.dps)

                print("%s: %03d/%03d" % (side, pic_num + 1, s), round(offset, 1))
                xyz = []
                for x, y in xy:
                    p = points_triangulate(self.config, (x, y), offset, color=c, right=right)
                    r = math.sqrt(math.pow(p[0], 2) + math.pow(p[2], 2))
                    # Remove points larger than the scan table
                    if r < 110:
                        xyz.append(p)

                xyz_all.append([i, offset, xyz])

        for i in range(0, len(xyz_all)):
            if i == 0:
                xyz = calculate_normal_vector(xyz_all[i][2], xyz_all[i + 1][2], right)
            else:
                xyz = calculate_normal_vector(xyz_all[i][2], xyz_all[i - 1][2], right)
            xyz = [[x, y, z, r, g, b, xn, yn, zn] for x, y, z, r, g, b, xn, yn, zn, flip in xyz]
            points.extend(xyz)
        return points


def main():
    # parse command line options
    parser = argparse.ArgumentParser(description="parse scan images", add_help=False)
    parser.add_argument("-H", "--help", help="show help", action="store_true", dest="show_help")
    parser.add_argument("-s", "--scan", help="scan dir", default=argparse.SUPPRESS, action="store", dest="path")
    args = parser.parse_args()

    show_help = args.show_help
    if show_help:
        parser.print_help()
        return
    path = args.path
    if len(path) == 0:
        print('-p / --path is required.')
        return
    try:
        parser = ScanParser(path)
        parser.parse()
    except:
        print("Parse failed.")


if __name__ == "__main__":
    main()