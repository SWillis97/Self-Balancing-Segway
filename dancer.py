import pyb
from pyb import LED, Pin, Timer, Switch

class Dancer:
    def __init__(self, theta, tilt):
        self.beatnum = 0
        self.original_set_point = theta
        self.current_move_left = False
        self.current_move_right = False
        self.current_set_point = 0
        self.dancing_duration = 0
        self.tic = 0
        self.forward_offset = self.original_set_point + tilt
        self.backward_offset = self.original_set_point - tilt
    def music_dance(self):

            pass
    def dance(self, dance_move):

        if self.dancing_duration >= pyb.millis() - self.tic:
            return self.current_move_left, self.current_move_right, self.current_set_point

        else:

            if dance_move == "r":
                self.current_move_left = False
                self.current_move_right = False
                self.current_set_point = self.original_set_point
                self.tic = pyb.millis()
                self.dancing_duration = 0  #enter in ms

            if dance_move == "w":
                self.current_move_left = False
                self.current_move_right = False
                self.current_set_point = self.forward_offset
                self.tic = pyb.millis()
                self.dancing_duration = 800

            if dance_move == "s":
                self.current_move_left = False
                self.current_move_right = False
                self.current_set_point = self.backward_offset
                self.tic = pyb.millis()
                self.dancing_duration = 800

            if dance_move == "e": # forward right
                self.current_move_left = True
                self.current_move_right = False
                self.current_set_point = self.forward_offset
                self.tic = pyb.millis()
                self.dancing_duration = 800

            if dance_move == "q": # forward left
                self.current_move_left = False
                self.current_move_right = True
                self.current_set_point = self.forward_offset
                self.tic = pyb.millis()
                self.dancing_duration = 800

            if dance_move == "a": # backward left
                self.current_move_left = False
                self.current_move_right = True
                self.current_set_point = self.backward_offset
                self.tic = pyb.millis()
                self.dancing_duration = 800

            if dance_move == "d": # backward right
                self.current_move_left = True
                self.current_move_right = False
                self.current_set_point = self.backward_offset
                self.tic = pyb.millis()
                self.dancing_duration = 800


        return self.current_move_left, self.current_move_right, self.current_set_point
