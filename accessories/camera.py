import subprocess
import cv2
from time import sleep
from picamera2 import Picamera2, Preview


hdr = False

picam2 = Picamera2()
preview_config = picam2.create_still_configuration(main={"size": (640, 360), "format": "XBGR8888"}, lores={"size": (320, 180)}, display="main")
save_config = picam2.create_still_configuration(main={"size": (1920, 1080), "format": "XBGR8888"})


configs = {
    "preview": preview_config,
    "save": save_config
}


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
    pos = 1000.0 / distance
    picam2.set_controls({"AfMode": 0, "LensPosition": pos})
    sleep(3)


def set_config(value):
    config = configs[value]
    picam2.align_configuration(config)
    picam2.switch_mode(config)
    sleep(0.5)


def capture_file(f_name):
    buffer = get_buffer()
    cv2.imwrite(f_name, buffer)


def get_buffer():
    img = picam2.capture_array()
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img


def get_jpg_buffer():
    img = get_buffer()
    ret, buffer = cv2.imencode('.jpg', img)
    if ret:
        return buffer
    else:
        raise Exception()


picam2.start_preview(Preview.NULL)
picam2.align_configuration(preview_config)
picam2.configure(preview_config)

picam2.start()
sleep(1)

set_focus_mm(300.0)
sleep(5)