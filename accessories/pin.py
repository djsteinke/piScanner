import RPi.GPIO as GPIO
from accessories.stepper_motor import sleep_us


GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)


class Pin(object):
    def __init__(self, pin):
        self._pin = pin
        GPIO.setup(self._pin, GPIO.OUT)
        self.off()

    def on(self, pulse=0):
        GPIO.output(self._pin, GPIO.HIGH)
        if pulse > 0:
            sleep_us(pulse)
            self.off()

    def off(self):
        GPIO.output(self._pin, GPIO.LOW)
