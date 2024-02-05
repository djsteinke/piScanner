import io
import subprocess
import cv2
from time import sleep
from picamera2 import Picamera2, Preview

hdr = False


def enable_hdr():
    global hdr
    _hdr(1)
    hdr = True


def disable_hdr():
    global hdr
    _hdr(0)
    hdr = False


def _hdr(enable):
    # v4l2-ctl --set-ctrl wide_dynamic_range=0 -d /dev/v4l-subdev0
    subprocess.run(['v4l2-ctl', '--set-ctrl', f'wide_dynamic_range={enable}', '-d', '/dev/v4l-subdev0'])


def set_focus_mm(distance):
    camera.set_focus_mm(distance)


def set_config(value):
    camera.set_config(value)


def capture_file(f_name):
    buffer = camera.get_buffer()
    cv2.imwrite(f_name, buffer)


def capture_file_cam(f_name):
    camera.capture_file(f_name)


def get_rotated_buffer():
    img = camera.get_buffer()
    img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return img


def get_jpg_buffer(x, y):
    img = get_rotated_buffer()
    h, w = img.shape[:2]
    x = int(x / 3)
    y = int(y / 3)
    img = cv2.line(img, (x, 0), (x, h), (0, 0, 255), 3)
    img = cv2.line(img, (0, y), (w, y), (0, 0, 255), 3)
    #h /= 3
    #w /= 3
    #img = cv2.resize(img, (int(w), int(h)), interpolation=cv2.INTER_AREA)
    ret, buffer = cv2.imencode('.jpg', img)
    if ret:
        return buffer
    else:
        raise Exception()


class Camera(object):
    def __init__(self):
        self.picam2: Picamera2 = None
        self.configs = {}

    def start(self):
        if self.picam2 is None:
            self.picam2 = Picamera2()
        self.create_configs()
        self.picam2.start_preview(Preview.NULL)
        self.set_config('save')
        self.picam2.start()
        sleep(1)

    def create_configs(self):
        preview_config = self.picam2.create_still_configuration(main={"size": (640, 360), "format": "XBGR8888"})
        save_config = self.picam2.create_still_configuration(main={"size": (1920, 1080), "format": "BGR888"}, lores={"size": (640, 360)})
        self.configs['save'] = save_config
        self.configs['preview'] = preview_config

    def set_focus_mm(self, distance):
        pos = 1000.0 / distance
        self.picam2.set_controls({"AfMode": 0, "LensPosition": pos})
        sleep(1)

    def set_config(self, value):
        config = self.configs[value]
        self.picam2.align_configuration(config)
        self.picam2.switch_mode(config)
        sleep(0.5)
        print('config set:', value)

    def capture_file(self, f_name):
        self.picam2.capture_file(f_name)

    def get_buffer(self):
        img = self.picam2.capture_array("lores")
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return img


camera = Camera()
