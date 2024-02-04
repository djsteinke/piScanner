from camera import camera_configuration, CameraConfiguration

default_step_size = 1.8
default_micro_steps = 2.0


class ScannerConfiguration(object):
    def __init__(self, camera_config, stepper_config, right_laser_config, left_laser_config):
        self.camera: CameraConfiguration = camera_config
        self.stepper_motor: StepperMotorConfiguration = stepper_config
        self.right_laser: LaserConfiguration = right_laser_config
        self.left_laser: LaserConfiguration = left_laser_config


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
