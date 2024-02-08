import RPi.GPIO as GPIO
from accessories.pin import Pin


GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)


class Laser(object):
    def __init__(self, pin, right=True):
        self.pin = Pin(pin)
        self.right = right

    def on(self):
        self.pin.on()

    def off(self):
        self.pin.off()