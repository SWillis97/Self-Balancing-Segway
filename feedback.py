class Balance:
    def __init__(self, kp, kd, ki, theta):
        self.kp = kp
        self.kd = kd
        self.ki = ki

        self.error_accuml = 0
        self.target_pitch = theta
        self.base_set_point = theta
    def control(self, current_pitch, pitch_dot):

        error = current_pitch - self.target_pitch
        prop = self.kp * error
        self.error_accuml += (self.ki * error)
        de = self.kd * pitch_dot

        drive = prop + de + self.error_accuml

        """print("P: ", prop)
        print("I: ", self.error_accuml)
        print("D: ", de)
        print("drive: ", drive)"""
        return drive

    def reset_setpoint(self):
        self.target_pitch = self.base_set_point

    def new_setpoint(self, theta):
        self.target_pitch = theta
