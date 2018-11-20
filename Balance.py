import pyb
from pyb import LED, Pin, Timer, Switch
from oled_938 import OLED_938
from mpu6050 import MPU6050
import time
from feedback import Balance
from dancer import Dancer
import robot

### Motor Control
imu, oled, pot, A1, A2, B1, B2, motorA, motorB = robot.initalize_robot()

def forward(speed, move_left=False, move_right=False):
	A1.high()
	A2.low()
	B1.low()
	B2.high()
	if move_left:
		motorA.pulse_width_percent(speed*0.8)
		motorB.pulse_width_percent(speed)
	elif move_right:
		motorA.pulse_width_percent(speed)
		motorB.pulse_width_percent(speed*0.8)
	else:
		motorA.pulse_width_percent(speed)
		motorB.pulse_width_percent(speed)

def backward(speed, move_left=False, move_right=False):
	A1.low()
	A2.high()
	B1.high()
	B2.low()
	if move_left:
		motorA.pulse_width_percent(speed*0.8)
		motorB.pulse_width_percent(speed)
	elif move_right:
		motorA.pulse_width_percent(speed)
		motorB.pulse_width_percent(speed*0.8)
	else:
		motorA.pulse_width_percent(speed)
		motorB.pulse_width_percent(speed)

def tune_k(tune_p=False,tune_i=False,tune_d=False,s_point=False):
	global kp
	global kd
	global ki
	global set_point
	trigger = Switch()
	oled.clear()
	if tune_p:
		while not trigger():
			kp = 0 + (pot.read() * 20 /4095)
			oled.draw_text(0,10,"kp: {}" .format(kp))
			oled.display()
		while trigger():
		        pass

	if tune_i:
		while not trigger():
			ki = 0 + (pot.read() * 0.5 /4095)
			oled.draw_text(0,10,"ki: {}" .format(ki))
			oled.display()

	while trigger():
	        pass
	if tune_d:
	    while not trigger():
	        kd = -1 + (pot.read() * 2 /4095)
	        oled.draw_text(0,10,"Kd: {}" .format(kd))
	        oled.display()

	    while trigger():
	        pass

	if s_point:

	    while not trigger():
	        set_point = -0.5 + (pot.read() * 2 /4095)
	        oled.draw_text(0,10,"set point: {}" .format(set_point))
	        oled.display()

	oled.clear()
	oled.draw_text(0,10,"Kp: {}" .format(kp))
	oled.draw_text(0,20,"Ki: {}" .format(ki))
	oled.draw_text(0,30,"Kd: {}" .format(kd))
	oled.draw_text(0,40,"set point: {}" .format(set_point))
	oled.display()
	time.sleep(1)
	oled.clear()


def comp_filter(dt, orginal_pitch):

    alpha = 0.95
    theta = imu.pitch()

    pitch_dot = imu.get_gy()
    updated_pitch = alpha*(orginal_pitch + pitch_dot*dt) + (1-alpha)*theta

    return updated_pitch, pitch_dot

def systems_green():
    oled.clear()
    oled.draw_text(0,20,"Robot Running ....")
    time.sleep(1)
    oled.display()
    oled.clear()


# CONTROL PANNEL #
set_point = 0.55
current_pitch = 0
kp = 5.3
ki = 0.45
kd = 0.3
offset = 1

debug = False
tune = False



if tune:
    tune_k(tune_i = True, s_point=True)

controller = Balance(kp,kd,ki,set_point)
dance_controller = Dancer(set_point)

tic = pyb.micros()
systems_green()

while True:

	dt = pyb.micros() - tic
	if dt > 5000 :
		current_pitch, pitch_dot = comp_filter(dt*0.000001, current_pitch)
		drive_signal = controller.control(current_pitch, pitch_dot)
		move = "r" beat
		move_left, move_right, new_set_point = dance_controller.dance(move)
		controller.new_setpoint(new_set_point)

		if drive_signal > 100:
			backward(100) # no move left or right b/c balancing is more important

		elif drive_signal < -100:
			forward(100)

		elif drive_signal < 0:
			forward(abs(drive_signal) + 5, move_left, move_right)

		else:
			backward(abs(drive_signal * offset) + 5, move_left, move_right)


		tic = pyb.micros()

		if debug:
			oled.clear()
			oled.draw_text(0,10,"Drive Signal: {}" .format(drive_signal))
			oled.draw_text(0,40,"Robot pitch: {}" .format(current_pitch))

			oled.display()
