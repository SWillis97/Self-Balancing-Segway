'''
-------------------------------------------------------
Name: PyBench Board Test Programme
Creator:  Peter Y K Cheung, Imperial College London
Date:   3 March 2017
Revision: 1.1
-------------------------------------------------------
This is a test programme to test the PyBench Board
	designed by Peter Cheung for Design Engineering Year 2 course
	on EEE.  This course covers three main topics:
	1. Signal processing
	2. System themory
	3. Feedback control
-------------------------------------------------------
The MIT License (MIT)
Copyright (c) 2014 Sebastian Plamauer, oeplse@gmail.com
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''	

import pyb
import math
import gc
from pyb import LED, USB_VCP, DAC, Timer, ADC, Pin, UART
from array import array
from oled_938 import OLED_938
from mpu6050 import MPU6050
from motor import DRIVE

# Define various ports, pins and peripherals
a_out = DAC(1, bits=12)
a_in = ADC(Pin('X12'))
pot = ADC(Pin('X11'))
mic = ADC(Pin('Y11'))
r_LED = LED(1)
g_LED = LED(2)
y_LED = LED(3)
b_LED = LED(4)

g_pitch = 0

#  Configure X2:4, X7 as setting input pin - pull_up to receive switch settings
s0=Pin('Y3',pyb.Pin.IN,pyb.Pin.PULL_UP)
s1=Pin('X6',pyb.Pin.IN,pyb.Pin.PULL_UP)

# I2C connected to Y9, Y10 (I2C bus 2) and Y11 is reset low active
oled = OLED_938(pinout={'sda': 'Y10', 'scl': 'Y9', 'res': 'Y8'}, height=64,
                   external_vcc=False, i2c_devid=61)
oled.poweron()
oled.init_display()

# IMU connected to X9 and X10
imu = MPU6050(1, False)

#  initialize UART on Y1 and Y2
uart = UART(6)
uart.init(9600, bits=8, parity = None, stop = 2)\

# create motor class to drive motors
motor = DRIVE()

# Create the samples in sine array
N_samp = 128
sig_freq = 1000
sine_array = array('H', 0 for i in range(N_samp))  # reserve space for array
data_array = array('H', 0 for i in range(128))  # reserve space for data array
for i in range(N_samp):
	sine_array[i] = int(2048 + 1800*math.sin(2*math.pi*i/N_samp))

'''
Define various test functions
'''
def read_sw():
	value = 3 - (s0.value() + 2*s1.value())
	if (not s0.value()):
		y_LED.on()
	if (not s1.value()):
		g_LED.on()
	return value
	
def	plot_sig(signal,message):
	index = len(signal)
	if index >= 128:
		step = min(index,int(index/128))
	else:
		step = 1
	oled.clear()
	oled.draw_text(0,0,message)
	x = 127
	max_sig = max(max(signal),3000)
	min_sig = min(min(signal),1000)
	range_sig = max_sig - min_sig
	for i in range(0,index,step):
		y = 63 - int((signal[i] - min_sig)*63/range_sig)
		oled.set_pixel(x,y,True)
		x = x - 1
	oled.display()

def sine_gen():
	g_LED.on()
	a_out.write(0)
	a_out.write_timed(sine_array, pyb.Timer(4, freq=int(N_samp*sig_freq)), mode=DAC.CIRCULAR)
	n_cycles = (pot.read()/500)+1
	triggered = False
	T_WINDOW = 30
	time_out = False;
	tic = pyb.millis()
	while not triggered or time_out:		# always trigger at the same place
		a_trigger = a_in.read()
		a_slope = (a_trigger - a_in.read()) >= 0
		triggered = (a_trigger <= 2048 + T_WINDOW) & (a_trigger >= 2048 - T_WINDOW) & a_slope
		toc = (pyb.millis() - tic)
		if toc > 1000:
			time_out = True
			print('Trigger Time Out')			
	a_in.read_timed(data_array, pyb.Timer(6, freq=sig_freq*N_samp/n_cycles))
	plot_sig(data_array,"Sine Gen & Capture Test")
	try:
		send_uart("Sinewave")
	except OSError:
		print('UART send error')
 
def test_mic():
	g_LED.on()
	samp_freq = (pot.read()/4)+500  # minimum 500 Hz sampling
	mic.read_timed(data_array, pyb.Timer(5, freq=samp_freq))
	plot_sig(data_array,"Microphone Signal")
	try:
		send_uart("Microphone Test")
	except OSError:
		print('UART send error')
 
def test_imu(dt):
	global g_pitch
	alpha = 0.7    # larger = longer time constant
	y_LED.on()
	pitch = int(imu.pitch())
	roll = int(imu.roll())
	g_pitch = alpha*(g_pitch + imu.get_gy()*dt*0.001) + (1-alpha)*pitch
	# show graphics
	y = 32 - int(31*pitch/100)
	y = max(min(y,63) ,0)
	x = int(63*roll/100) + 64
	x = max(min(x,127), 0)
	oled.clear()
	oled.draw_square(x,y,2,1)
	oled.line(96, 26, pitch, 24, 1)
	oled.line(32, 26, g_pitch, 24, 1)
	oled.draw_text(0,0," Raw | PITCH |")
	oled.draw_text(83,0, "filtered")
	oled.display()	
	try:
		send_uart("IMU Test")
	except OSError:
		print('UART send error')
	
def send_uart(message):
	for i in range(len(message)):
		uart.writechar(ord(message[i]))
	uart.writechar(13)
	uart.writechar(10)
	
def test_motor():
	r_LED.on()
	speed = int((pot.read()-2048)*200/4096);
	motor.set_speed(speed)
	motor.set_turn(0)
	motor.drive()
	actual_speed = motor.get_speedB()

	oled.clear()
	oled.draw_text(0,0,"Testing Motors")

	oled.draw_text(0,10,'PWM:{:4d}'.format(speed))
	oled.draw_text(0,20,'SpeedA:{:5.2f} rps'.format(motor.speedA/39))	
	oled.draw_text(0,30,'SpeedB:{:5.2f} rps'.format(motor.speedB/39))	

	oled.display()
	try:
		send_uart("Motor Test")
	except OSError:
		print('UART send error')
    
tic = pyb.millis()		
while True:
#	y_LED.off()
	g_LED.off()
	r_LED.off()
	b_LED.toggle()
	if (read_sw()==0):
		motor.stop()
		test_mic()
	elif (read_sw()==1):
		motor.stop()
		toc = pyb.millis()
		test_imu(toc-tic)
		tic = pyb.millis()
	elif (read_sw()==2):
		test_motor()
	elif (read_sw()==3):
		motor.stop()
		sine_gen()
