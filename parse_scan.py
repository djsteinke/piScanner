import argparse


class ScanParser(object):
    def __init__(self, path):
        self.path = path

    def parse(self):
        print(f'parsing {self.path}')


def main():
    # parse command line options
    parser = argparse.ArgumentParser(description="parse scan images", add_help=False)
    parser.add_argument("-H", "--help", help="show help", action="store_true", dest="show_help")
    parser.add_argument("-p", "--path", help="scan path", default=argparse.SUPPRESS, action="store", dest="path")
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