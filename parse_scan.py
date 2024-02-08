import argparse
import os.path
import glob

import scanner_paths
from scan import ScanDetails

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

    def parse(self):
        if os.path.exists(self.path):
            print(f'parsing {self.path}')
        else:
            print(f'No scan found at {self.path}')
            return

        try:
            details = ScanDetails.load(self.path)
        except Exception as e:
            return

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


        print("I: processing %d steps" % details['steps'])

        if len(right) > 0:
            right.sort()
            # points = points_process_images(right, color=color, right=True)

        if len(left) > 0:
            left.sort()
            # left = points_process_images(left, color=color, right=False)
            # points.extend(left)

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

    parser = ScanParser(path)
    parser.parse()


if __name__ == "__main__":
    main()