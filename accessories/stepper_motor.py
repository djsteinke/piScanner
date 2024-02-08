import RPi.GPIO as GPIO
import time

from accessories.pin import Pin
from static.common import get_us_as_sec, sleep_us

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

pulse_w = 20    # us
ppr = 400.0       # pulse/rot
rpm_max = 100.0
rpm_min = 0.5
rpm_acc = 10.0    # rot/m/s
mps_min = int(60000000.0 / rpm_max / ppr) - pulse_w
mps_max = 100000.0

spd = 8.0           # steps / deg


class StepperMotor(object):
    def __init__(self, enb_pin: int, dir_pin: int, pul_pin: int):
        self.DIR = Pin(dir_pin)
        self.ENB = Pin(enb_pin)
        self.PUL = Pin(pul_pin)
        self._rpm = 0.0
        self._mps = mps_min
        self._last_step_us = 0
        self._steps_to_full = 0
        self._enabled = False
        self.disable()

    def enable(self):
        self.ENB.on()
        self._enabled = True

    def disable(self):
        self.ENB.off()
        self._enabled = False

    def _reset(self):
        self._rpm = 0.0
        self._steps_to_full = 0
        self._mps = mps_min

    def step(self, steps, cw):
        if cw:
            self.DIR.off()
        else:
            self.DIR.on()

        self._last_step_us = int(time.time_ns() / 1000.0)
        for n in range(0, steps):
            self._last_step_us = int(time.time_ns() / 1000.0)
            self.PUL.on(pulse_w)
            sleep_us(self._mps)
            acc = True if (self._steps_to_full == 0 and n < (steps - n)) or (self._steps_to_full > 0 and steps - self._steps_to_full > n) else False
            if not acc and n % 3 == 0:
                pass
            if self._update_mps(acc) and self._steps_to_full == 0:
                self._steps_to_full = n
        self._reset()

    def rotate(self, degrees: float, cw=True):
        steps = int(degrees * spd)
        self.step(steps, cw)

    def _update_mps(self, acc):
        curr_us = int(time.time_ns()/1000.0)
        rpm_delta = rpm_acc * get_us_as_sec(curr_us - self._last_step_us)
        if acc:
            self._rpm += rpm_delta
            self._rpm = self._rpm if self._rpm < rpm_max else rpm_max
        else:
            self._rpm -= rpm_delta
            self._rpm = self._rpm if self._rpm > rpm_min else rpm_min
        p_tol = int(60000000.0 / self._rpm / ppr)
        self._mps = p_tol - pulse_w
        if self._mps >= mps_max:
            self._mps = mps_max
        elif self._mps < mps_min:
            self._mps = mps_min
        return True if self._rpm >= rpm_max else False

    @property
    def enabled(self):
        return self._enabled


stepper = StepperMotor(3, 5, 7)
