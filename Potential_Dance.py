import pyb
from pyb import LED, Pin, Timer, Switch, ADC, UART
from oled_938 import OLED_938
from mpu6050 import MPU6050
import time
from feedback import Balance
from dancer import Dancer
import robot
from remote import user_move
from array import array
from DanceMoves_Sam import *
from mic import MICROPHONE

import micropython
micropython.alloc_emergency_exception_buf(100)

def forward(speed, move_left=False, move_right=False):
	A1.high()
	A2.low()
	B1.low()
	B2.high()
	if move_left:
		motorA.pulse_width_percent(speed*0.7)
		motorB.pulse_width_percent(speed)
	elif move_right:
		motorA.pulse_width_percent(speed)
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
		motorB.pulse_width_percent(speed)
	elif move_right:
		motorA.pulse_width_percent(speed)
		motorB.pulse_width_percent(speed*0.7)
	else:
		motorA.pulse_width_percent(speed)
		motorB.pulse_width_percent(speed)

### Motor Control
imu, oled, pot, A1, A2, B1, B2, motorA, motorB = robot.initalize_robot()



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
set_point = 0.51
current_pitch = 0
kp = 5.3
ki = 0.45
kd = 0.3
offset = 1

mic = ADC(Pin('Y11'))
sample_timer = pyb.Timer(7, freq=8000)
# define ports for microphone, LEDs and trigger out (X5)
micro = MICROPHONE(sample_timer, mic, 160)

b_LED = LED(4)

N = 160				# size of sample buffer s_buf[]
s_buf = array('H', 0 for i in range(N))  # reserve buffer memory
ptr = 0				# sample buffer index pointer
buffer_full = False	# semaphore - ISR communicate with main program

def energy(buf):	# Compute energy of signal in buffer
	sum = 0
	for i in range(len(buf)):
		s = buf[i] - MIC_OFFSET	# adjust sample to remove dc offset
		sum = sum + s*s			# accumulate sum of energy
	return sum



# Define constants for main program loop - shown in UPPERCASE
M = 50						# number of instantaneous energy epochs to sum
BEAT_THRESHOLD = 2.4		# threshold for c to indicate a beat
SILENCE_THRESHOLD = 1.3		# threshold for c to indicate silence

# initialise variables for main program loop
e_ptr = 0					# pointer to energy buffer
e_buf = array('L', 0 for i in range(M))	# reserve storage for energy buffer
sum_energy = 0				# total energy in last 50 epochs
oled.draw_text(0,20, 'Ready to GO')	# Useful to show what's happening?
oled.display()
pyb.delay(100)
			# mark time now in msec

moves = read_file('list_of_moves.txt')
current_move = 0



debug = False
tune = False



if tune:
    tune_k(tune_i = True, s_point=False, tune_d =False)

controller = Balance(kp,kd,ki,set_point)
dance_controller = Dancer(set_point)
tic_detect = pyb.millis()
tic = pyb.micros()
systems_green()
move = 'r'

while True:

	dt = pyb.micros() - tic
	if dt > 5000 :
		current_pitch, pitch_dot = comp_filter(dt*0.000001, current_pitch)
		drive_signal = controller.control(current_pitch, pitch_dot)
		move = user_move()
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



		if micro.buffer_full:		# semaphore signal from ISR - set if buffer is full

			b_LED.off()
			# Calculate instantaneous energy
			E = micro.inst_energy()

			# compute moving sum of last 50 energy epochs
			sum_energy = sum_energy - e_buf[e_ptr] + E
			e_buf[e_ptr] = E		# over-write earlest energy with most recent
			e_ptr = (e_ptr + 1) % M	# increment e_ptr with wraparound - 0 to M-1

			# Compute ratio of instantaneous energy/average energy
			c = E*M/sum_energy

			if (pyb.millis()-tic_detect > 500):	# if more than 500ms since last beat
				print(c)
				if (c>BEAT_THRESHOLD): # look for a beat
					print('I made it')
					tic_detect = pyb.millis()
					b_LED.on() # reset tic
					move = readmove(moves,current_move,25, False)					# beat found, flash blue LED
					current_move += 1
					if current_move == 8:
						current_move = 0

				elif(pyb.millis()-tic_detect > 2000):
					tic_detect = pyb.millis() 	# reset tic
					move = readmove(moves,current_move,25, False)					# beat found, flash blue LED
					current_move += 1
					if current_move == 8:
						current_move = 0

			micro.set_buffer_empty				# reset status flag
