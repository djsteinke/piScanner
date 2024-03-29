import os
import pickle
from configuration.camera import CameraConfiguration
from scanner_paths import config_path
from accessories.stepper_motor import StepperMotor

default_step_size = 1.8
default_micro_steps = 2

pickle_file = 'configuration.p'


class ScannerConfiguration(object):
    def __init__(self, camera_config, stepper_config, right_laser_config, left_laser_config):
        self.camera: CameraConfiguration = camera_config
        self.stepper_motor: StepperMotorConfiguration = stepper_config
        self.right_laser: LaserConfiguration = right_laser_config
        self.left_laser: LaserConfiguration = left_laser_config

    def get_stepper_motor(self):
        return StepperMotor(self.stepper_motor.enable_pin, self.stepper_motor.dir_pin, self.stepper_motor.pulse_pin)


    def save(self):
        source = os.path.join(config_path, pickle_file)
        pickle.dump(self, open(source, "wb"))

    @staticmethod
    def load():
        source = os.path.join(config_path, pickle_file)
        try:
            with open(source, 'rb') as file:
                config = pickle.load(file)
        except:
            config = ScannerConfiguration(CameraConfiguration(), StepperMotorConfiguration(3, 5, 7),
                                          LaserConfiguration(11), LaserConfiguration(13))
            config.save()
        # print(config.camera.new_camera_mtx)
        return config


class LaserConfiguration(object):
    def __init__(self, pin, angle=30.0):
        self.pin = pin
        self.angle = angle


class StepperMotorConfiguration(object):
    def __init__(self, enable_pin, dir_pin, pulse_pin, step_size=default_step_size, micro_steps=default_micro_steps):
        self.enable_pin = enable_pin
        self.dir_pin = dir_pin
        self.pulse_pin = pulse_pin
        self.step_size = step_size
        self.micro_steps = micro_steps
