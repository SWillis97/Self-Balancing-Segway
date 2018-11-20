import pyb
from pyb import LED, Pin, Timer, Switch, ADC
from oled_938 import OLED_938
from mpu6050 import MPU6050
import time
from feedback import Balance
from dancer import Dancer
import robot
from remote import user_move
import os

import micropython
micropython.alloc_emergency_exception_buf(100)
### Motor Control
imu, oled, pot, A1, A2, B1, B2, motorA, motorB = robot.initalize_robot()

def forward(speed, move_left=False, move_right=False):
	A1.high()
	A2.low()
	B1.low()
	B2.high()
	if move_left:
		motorA.pulse_width_percent(speed*0.7)
		motorB.pulse_width_percent(speed*1.3)
	elif move_right:
		motorA.pulse_width_percent(speed*1.3)
		motorB.pulse_width_percent(speed*0.7)
	else:
		motorA.pulse_width_percent(speed)
		motorB.pulse_width_percent(speed)

def backward(speed, move_left=False, move_right=False):
	A1.low()
	A2.high()
	B1.high()
	B2.low()
	if move_left:
		motorA.pulse_width_percent(speed*0.7)
		motorB.pulse_width_percent(speed*1.3)
	elif move_right:
		motorA.pulse_width_percent(speed*1.3)
		motorB.pulse_width_percent(speed*0.7)
	else:
		motorA.pulse_width_percent(speed)
		motorB.pulse_width_percent(speed)

def reset_txt():
	kp_saved = open('kp_store.txt','w')
	kp_saved.write('5.0')
	kp_saved.close()

	ki_saved = open('ki_store.txt','w')
	ki_saved.write('0.45')
	ki_saved.close()

	kd_saved = open('kd_store.txt','w')
	kd_saved.write('0.3')
	kd_saved.close()

def tune_k(tune_p=True,tune_i=True,tune_d=True):
	global kp
	global kd
	global ki

	trigger = Switch()
	oled.clear()

	kp_saved = open('kp_store.txt','r')
	last_kp = kp_saved.read()
	last_kp = float(last_kp[:])
	kp_saved.close()

	ki_saved = open('ki_store.txt','r')
	last_ki = ki_saved.read()
	last_ki = float(last_ki[:])
	ki_saved.close()


	kd_saved = open('kd_store.txt','r')
	last_kd = kd_saved.read()
	last_kd = float(last_kd[:])
	kd_saved.close()

	print(last_kp)
	print(last_ki)
	print(last_kd)

	if tune_p:
		while not trigger():
			time.sleep(0.001)
			kp = float(last_kp) + ((pot.read() /4095) - 0.5) * 0.5
			oled.draw_text(0,10,"kp: {}" .format(kp))
			oled.display()
		while trigger():
		        pass

	if tune_i:
		while not trigger():
			time.sleep(0.001)
			ki = float(last_ki) + ((pot.read() /4095) - 0.5) * 0.5
			oled.draw_text(0,10,"ki: {}" .format(ki))
			oled.display()

		while trigger():
			pass

	if tune_d:
			while not trigger():
				time.sleep(0.001)
				kd = float(last_kd) + ((pot.read()/4095) - 0.5) * 0.5
				oled.draw_text(0,10,"Kd: {}" .format(kd))
				oled.display()

			while trigger():
				pass

	kp_store = open('kp_store.txt','w')
	kp_store.write(str(kp))
	kp_store.close()

	ki_store = open('ki_store.txt','w')
	ki_store.write(str(ki))
	ki_store.close()

	kd_store= open('kd_store.txt','w')
	kd_store.write(str(kd))
	kd_store.close()

	#print(kp)
	#print(ki)
	#print(kd)

	oled.clear()
	oled.draw_text(0,10,"Kp: {}" .format(kp))
	oled.draw_text(0,20,"Ki: {}" .format(ki))
	oled.draw_text(0,30,"Kd: {}" .format(kd))
	oled.display()
	time.sleep(0.5)
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

def set_point_tune():
	global set_point
	trigger = Switch()
	oled.clear()
	while not trigger():
			time.sleep(0.001)
			set_point = 0 + ((pot.read()/4095)) * 2
			oled.draw_text(0,10,"set point: {}" .format(set_point))
			oled.display()
	oled.clear()

def tilt_tune():
	global tilt
	trigger = Switch()
	oled.clear()
	while not trigger():
			time.sleep(0.001)
			tilt = 0 + ((pot.read()/4095)) * 2
			oled.draw_text(0,10,"Tilt: {}" .format(tilt))
			oled.display()
	oled.clear()

# CONTROL PANNEL #
current_pitch = 0
set_point = 0.25
tilt = 1.22
kp = 5.45
ki = 0.55
kd = 0.45

offset = 1

debug = False
tune = False
#reset_txt()
#set_point_tune()
#tilt_tune()

if tune:
    tune_k(tune_p = True, tune_i = True, tune_d =True)

controller = Balance(kp,kd,ki,set_point)
dance_controller = Dancer(set_point, abs(tilt))

tic = pyb.micros()
systems_green()

while True:

	dt = pyb.micros() - tic
	if dt > 5000 :
		current_pitch, pitch_dot = comp_filter(dt*0.000001, current_pitch)

		drive_signal = controller.control(current_pitch, pitch_dot)
		move = user_move()

		if move != 'r':
			print(move)
		move_left, move_right, new_set_point = dance_controller.dance(move)
		#print(move_left, move_right, new_set_point)
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
