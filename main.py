from picamera2 import Picamera2, Preview
#from libcamera import controls
from time import sleep
import threading
import flaskApp
#import cv2

#camera = cv2.VideoCapture(0)


if __name__ == '__main__':
    picam2 = Picamera2()
    # camera_config = picam2.create_preview_configuration()
    # config = camera.create_video_configuration(main={"size": (640, 480)}, controls={"FrameDurationLimits": (15000, 15000)}, buffer_count=2)
    camera_config = picam2.create_still_configuration(main={"size": (1920, 1080)}, lores={"size": (640, 480)},
                                                      display="lores")
    picam2.configure(camera_config)
    picam2.start_preview(Preview.NULL)
    sleep(2)
    # picam2.configure(camera_config)
    #picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": 0.0})
    sleep(2)
    picam2.start()
    flaskApp.start_app()
    flaskApp.picam2 = picam2

    picam2.capture_file('test.jpg')


