import time


def get_us_as_sec(val):
    return val / 1000000.0


def get_sec_as_us(val):
    return val * 1000000.0


def sleep_us(val):
    us = get_us_as_sec(val)
    time.sleep(us)
