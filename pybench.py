'''
-------------------------------------------------------
Name: PyBench (for Pyboard electronics Workbench)
Creator:  Peter Y K Cheung, Imperial College London
Date:   4 March 2017
Revision: 2.0 (add support for drone motors)
-------------------------------------------------------
This is driver class to use the Pyboard as a simple signal generation and signal capture.
Pyboard is mounted on a PyBench add-on card for use by Design Engineering 2nd year
on my course DE 2.3 - Systems, Signals and Control.

I used Adafruit's 1.3" OLED display and the SSD1306 driver if it is present.
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
from pyb import Pin, Timer, DAC, ADC
from array import array
from oled_938 import OLED_938
from mpu6050 import MPU6050
from motor import DRIVE
from struct import unpack

# Constants
BLANK_LINE          = "                   "

class PYBENCH(object):

	def __init__(self, pins):
			
		if pins['a_out'] == 'X5':
			self.dac = pyb.DAC(1, bits=12)
		else:
			self.dac = pyb.DAC(2, bits=12)
		self.adc = pyb.ADC(pins['a_in'])
		self.mic = pyb.ADC(pins['mic'])
		self.pot = pyb.ADC(pins['pot'])
		
		# Virtual Instrument Parameters at start up
		self.sig_freq = 1000.0		# sinewave frequency
		self.dc_v = 2020			# DC voltage level
		self.max_v = 4095  		# maximum voltage
		self.min_v = 0			# minimum voltage
		self.N_samp = 256		# number of sample in one cycle to generate
		self.samp_freq = 100
		self.buf_size = 4096
		self.N_window = 1000
		self.duty_cycle = 90
		self.function = "Idle"
		self.buf_max = 8192
		self.motor_direction = 0	# forward
		
		self.dac.write(0)
		
		# Initialise OLED display
		self.test_dev = pyb.I2C('Y',pyb.I2C.MASTER)
		if (not self.test_dev.scan()):
			self.oled = None
		else:
			self.oled = OLED_938(pinout={'sda': 'Y10', 'scl': 'Y9', 'res': 'Y8'}, 
					height=64,
                   external_vcc=False, i2c_devid=61)
 
			self.oled.poweron()
			self.oled.init_display()
			self.oled.draw_text(0, 0, "-- PyBench v2.0 --")
			self.oled.draw_text(30, 40, "** READY **")
			self.oled.display()
			
		# Initialise IMU - connected to I2C(1) - add handling missing IMU later
		self.imu = MPU6050(1, False)
		
		# create motor class to drive motors
		self.motor = DRIVE()
			
	def display_present(self):
		if (not self.oled):
			return False
		else:
			return True
				
	def volts (self,value):
		return (value*3.3/4096)
		
	def put(self, value):
		self.function = "DC"
		self.dc_v = value
		self.dac.write(value)
		
	def out(self, value):
		self.dc_v = value
		self.dac.write(value)
		
	def put_sine(self):
		self.function = "AC"
		if (self.display_present()):
			s = "AC %4.2fV" % self.volts(self.min_v) + " - %4.2fV" % self.volts(self.max_v)
			self.oled.draw_text (0, 10, s)
			self.oled.draw_text (10, 20, "Fsig : %5.1fHz" % self.sig_freq)
			self.oled.draw_text (10, 30, "Fsamp: %5.1fHz" % self.samp_freq)
			self.oled.display()
		pyb.delay(500)
		# Create the samples in sine array
		self.dac.write(0)  	# Quirk of Pyboard - need to write to DAC once first
		sine_array = array('H', 0 for i in range(self.N_samp))
		mid_v = (self.max_v + self.min_v)/2
		amp_v = (self.max_v - self.min_v)/2
		for i in range(self.N_samp):
			sine_array[i] = int(mid_v
					+ amp_v*math.sin(2*math.pi*i/self.N_samp))
		# Generate the sinewave
		self.dac.write_timed(sine_array, 
			pyb.Timer(2, freq=int(self.N_samp*self.sig_freq)), mode=DAC.CIRCULAR)

	def put_triangle(self):
		self.function = "TR"
		if (self.display_present()):
			s = "TR %4.2fV" % self.volts(self.min_v) + " - %4.2fV" % self.volts(self.max_v)
			self.oled.draw_text (0, 10, s)
			self.oled.draw_text (10, 20, "Fsig: %5.1fHz" % self.sig_freq)
			self.oled.draw_text (10, 30, "Fsamp: %5.1fHz" % self.samp_freq)
			self.oled.display()
		pyb.delay(150)
		# Create the samples in triangle array
		self.dac.write(0)  	# Quirk of Pyboard - need to write to DAC once first
		delta_v = (self.max_v - self.min_v)/(0.5*self.N_samp)
		tri_array = array('H', 0 for i in range(self.N_samp))  
	 	for i in range(int(self.N_samp/2)):
			tri_array[i] = int(self.min_v + i*delta_v)
			tri_array[self.N_samp-i-1] = tri_array[i]
		# Generate the triangular wave
		self.dac.write_timed(tri_array, 
			pyb.Timer(2, freq=int(self.N_samp*self.sig_freq)), mode=DAC.CIRCULAR)
	
	def put_square(self):
		self.function = "SQ"
		if (self.display_present()):
			s = "SQ %4.2fV" % self.volts(self.min_v) + " - %4.2fV" % self.volts(self.max_v)
			self.oled.draw_text (0, 10, s)
			self.oled.draw_text (10, 20, "Fsig : %5.1fHz" % self.sig_freq)
			self.oled.draw_text (10, 30, "Duty_cycle: %3d" % self.duty_cycle)
			self.oled.display()
		pyb.delay(150)
		# Create the samples in square array
		self.dac.write(0)  	# Quirk of Pyboard - need to write to DAC once first
		square_array = array('H', 0 for i in range(self.N_samp))
		h_index = int(self.N_samp*self.duty_cycle/100 + 0.5)
		for i in range(h_index):
			square_array[i] = int(self.max_v)
		for i in range (h_index, self.N_samp):
			square_array[i] = int(self.min_v)
		# Generate the triangular wave
		self.dac.write_timed(square_array, 
			pyb.Timer(2, freq=int(self.N_samp*self.sig_freq)), mode=DAC.CIRCULAR)

	def get(self):
		return self.adc.read()
		
	def get_mean(self,n):
		reading = 0
		for i in range(n):
			reading = reading + self.adc.read()
		return int((reading/n)+0.5)
		
	def get_block(self,n):
		# Create sample buffer
		s_buf = array('H', 0 for i in range(n))
		x=self.adc.read_timed(s_buf, pyb.Timer(5, freq=self.samp_freq))
		return (s_buf)
		
	def get_mic(self,n):
		# Create sample buffer
		s_buf = array('H', 0 for i in range(n))
		x=self.mic.read_timed(s_buf, pyb.Timer(5, freq=self.samp_freq))
		self.oled.draw_text (0, 20, "Get %4d MIC samples" % n)
		self.oled.display()
		return (s_buf)
		
	def write_message(self,message):
		h_index = min(len(message), 18)		# maximum message length is 18
		self.oled.draw_text(0, 53, ">> " + message[0:h_index])
		self.oled.display()
		pyb.delay(200)
		
	def set_max_v(self, value):
		self.max_v = min(4095, max(0, value))

	def set_min_v(self, value):
		self.min_v = min(4095, max(0, value))

	def set_sig_freq(self, value):
		self.sig_freq = min(3000.0,max(0.1,value/10.0))

	def set_samp_freq(self, value):
		self.samp_freq = min(30000.0, max(1.0,value))

	def set_duty_cycle(self, value):
		self.duty_cycle = min(100.0, max(0, value))
		
	def set_N_window(self, value):
		self.N_window = value
		
	def get_imu(self):
		accel = self.imu.get_accel_raw()
		gyro = self.imu.get_gyro_raw()
		return [accel, gyro]
		
	def get_accel(self):
		accel = self.imu.get_accel_raw()
		return accel

	def get_gyro(self):
		gyro = self.imu.get_gyro_raw()
		return gyro

	def set_motor_direction(self, value):
		self.motor_direction = value;

	def set_motor_speed(self, value):
		if(self.motor_direction==0):
			self.motor.left_forward(value)
			self.motor.right_forward(value)
		else:
			self.motor.left_back(value)
			self.motor.right_back(value)
		# Display message
		self.oled.draw_text(0,20,'Driving motor{:4d}'.format(value))	
		self.oled.display()
 
	def get_motor_speed(self):
		s_buf = array('H', 0 for i in range(2))
		speedA = self.motor.get_speedA()
		speedB = self.motor.get_speedB()		
		s_buf[0] = speedA
		s_buf[1] = speedB
		return(s_buf)
