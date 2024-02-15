import threading
import os
import pickle
from time import strftime, sleep
from scanner_paths import scans_path
from configuration.configuration import ScannerConfiguration
from accessories.laser import Laser
from accessories.camera import Camera

class ScanDetails(object):
    def __init__(self, degrees_per_step, dir_name):
        self.name = dir_name
        self.dps = degrees_per_step

    def save(self, path):
        source = os.path.join(path, 'details.p')
        pickle.dump(self, open(source, "wb"))

    @staticmethod
    def load(path):
        source = os.path.join(path, 'details.p')
        try:
            with open(source, 'rb') as file:
                return pickle.load(file)
        except:
            print(f'No details.p file found in {path}')
            raise Exception()

class Scan(object):
    def __init__(self, config: ScannerConfiguration, camera: Camera, right_laser=True, left_laser=False, color=False, degrees_per_step=10, degrees=360, callback=None):
        self.right_laser = right_laser
        self.left_laser = left_laser
        self.color = color
        self.degrees_per_step = degrees_per_step
        self.degrees = degrees
        self.callback = callback
        self.config = config
        self.camera = camera
        self.motor = config.get_stepper_motor()
        self.motor.enable()
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
        image_path = os.path.join(self.path, "images")
        os.makedirs(image_path)
        ScanDetails(degrees_per_step=self.degrees_per_step, dir_name=self.timestamp).save(self.path)

    def start(self):
        print('started', self.__dict__)
        threading.Timer(0.1, self.run).start()

    def run(self):
        image_path = os.path.join(self.path, "images")
        steps = int(self.degrees / self.degrees_per_step) + 1
        print(f'Scanning with {steps} steps.')
        for s in range(0, steps):
            if s > 0:
                self.motor.rotate(self.degrees_per_step)
            sleep(0.25)
            if self.color:
                self.camera.capture_file(os.path.join(image_path, f'color_%04d.jpg' % s))
            if self.left_laser:
                self.ll.on()
                sleep(0.1)
                self.camera.capture_file(os.path.join(image_path, f'left_%04d.jpg' % s))
                self.ll.off()
            if self.right_laser:
                self.rl.on()
                sleep(0.1)
                self.camera.capture_file(os.path.join(image_path, f'right_%04d.jpg' % s))
                self.rl.off()
        self.motor.disable()