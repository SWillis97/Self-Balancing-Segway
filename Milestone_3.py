import pyb
from pyb import LED, Pin, Timer, Switch, UART
from oled_938 import OLED_938
from mpu6050 import MPU6050
from Control_Zach_FB import initalize_robot
import micropython

micropython.alloc_emergency_exception_buf(100)
imu, oled, pot, A1, A2, B1, B2, motorA, motorB = initalize_robot()

mic = ADC(Pin('Y11'))
MIC_OFFSET = 152

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

def isr_sampling(dummy): 	# timer interrupt at 8kHz
	global ptr				# need to make ptr visible inside ISR
	global buffer_full		# need to make buffer_full inside ISR

	s_buf[ptr] = mic.read()	# take a sample every timer interrupt
	ptr += 1				# increment buffer pointer (index)
	if (ptr == N):			# wraparound ptr - goes 0 to N-1
		ptr = 0
		buffer_full = True	# set the flag (semaphore) for buffer full



# Create timer interrupt - one every 1/8000 sec or 125 usec
pyb.disable_irq()			# disable interrupt while configuring timer
sample_timer = pyb.Timer(7, freq=8000)	# set timer 7 for 8kHz
sample_timer.callback(isr_sampling)		# specify interrupt service routine
pyb.enable_irq()			# enable interrupt again

moves = read_file('list_of_moves.txt')
current_move = 0

e_ptr = 0					# pointer to energy buffer
e_buf = array('L', 0 for i in range(M))	# reserve storage for energy buffer
sum_energy = 0
tic = pyb.millis()			# mark time now in msec


# Define constants for main program loop - shown in UPPERCASE
M = 50						# number of instantaneous energy epochs to sum
BEAT_THRESHOLD = 2.4		# threshold for c to indicate a beat

trigger = pyb.Switch()

while not trigger():
	pyb.delay(1)

while trigger():
	pass

tic = pyb.millis()			# mark time now in msec


while True:				# Main program loop
	if buffer_full:		# semaphore signal from ISR - set if buffer is full
		b_LED.off()
		E = energy(s_buf) # compute moving sum of last 50 energy epochs
		sum_energy = sum_energy - e_buf[e_ptr] + E
		e_buf[e_ptr] = E		# over-write earlest energy with most recent
		e_ptr = (e_ptr + 1) % M	# increment e_ptr with wraparound - 0 to M-1
		c = E*M/sum_energy # Compute ratio of instantaneous energy/average energy


		if (pyb.millis()-tic > 500):	# if more than 500ms since last beat
			if (c>BEAT_THRESHOLD): # look for a beat
				tic = pyb.millis() # reset tic
				b_LED.on() # beat found, flash blue LED
				readmove(moves,current_move,25)
                if current_move == 9:
                    current_move = 0
                else:
                    current_move += 1

		buffer_full = False				# reset status flag
