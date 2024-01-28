from picamera2 import Picamera2, Preview
#from libcamera import controls
from time import sleep
import threading
import flaskApp
#import cv2

#camera = cv2.VideoCapture(0)
camera = Picamera2()
config = camera.create_video_configuration(
    main={"size": (640, 480)},
    controls={"FrameDurationLimits": (15000, 15000)}, #this should be about 60fps
    buffer_count=2
    )
camera.configure(config)
camera.start()
sleep(1) #time to let the camera start

if __name__ == '__main__':
    while True:
        if camera is not None:
            break
        sleep(1)
    #flaskApp.picam2 = camera
    flaskApp.start_app()


