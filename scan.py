import threading
import os
from time import strftime, sleep
from scanner_paths import scans_path
from configuration.configuration import ScannerConfiguration
from accessories.laser import Laser
from accessories.camera import Camera
from accessories.stepper_motor import StepperMotor

class Scan(object):
    def __init__(self, config: ScannerConfiguration, camera: Camera, motor: StepperMotor, right_laser=True, left_laser=False, color=False, degrees_per_step=10, degrees=360, callback=None):
        self.right_laser = right_laser
        self.left_laser = left_laser
        self.color = color
        self.degrees_per_step = degrees_per_step
        self.degrees = degrees
        self.callback = callback
        self.config = config
        self.camera = camera
        self.motor = motor
        self.ll = Laser(config.left_laser.pin, right=False)
        self.rl = Laser(config.right_laser.pin)
        self.ll.off()
        self.rl.off()
        self.path = ""
        self.timestamp = strftime('%Y%m%d%H%M%S')
        self.create_dir()

    def create_dir(self):
        self.path = os.path.join(scans_path, f"{self.timestamp}")  # create scans dir
        os.makedirs(self.path)
        self.path = os.path.join(self.path, "images")
        os.makedirs(self.path)

    def start(self):
        print('started', self.__dict__)
        threading.Timer(0.1, self.run).start()

    def run(self):
        steps = int(self.degrees / self.degrees_per_step) + 1
        print(f'Scanning with {steps} steps.')
        for s in range(0, steps):
            if s > 0:
                self.motor.rotate(self.degrees_per_step)
            sleep(0.5)
            if self.color:
                # TODO turn on light
                self.camera.capture_file(f'%s\\color_%04d.jpg' % (self.path, s))
            if self.left_laser:
                self.ll.on()
                sleep(0.2)
                self.camera.capture_file(f'%s\\left_%04d.jpg' % (self.path, s))
                self.ll.off()
            if self.right_laser:
                self.rl.on()
                sleep(0.2)
                self.camera.capture_file(f'%s\\right_%04d.jpg' % (self.path, s))
                self.rl.off()
