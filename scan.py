

class Scan(object):
    def __init__(self, right_laser=True, left_laser=False, color=False, degrees_per_step=10, degrees=360):
        self.right_laser = right_laser
        self.left_laser = left_laser
        self.color = color
        self.degrees_per_step = degrees_per_step
        self.degrees = degrees

    def start(self):
        print('started', self.__dict__)
