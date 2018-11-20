'''
-------------------------------------------------------
Name: motor
Creator:  Peter Y K Cheung, Imperial College London
Date:   28 December 2016
Revision: 1.0
-------------------------------------------------------
This is driver class controls the motors via the PyBench board.

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

import pyb, micropython
from pyb import Pin, Timer, ExtInt

micropython.alloc_emergency_exception_buf(100)

class DRIVE(object):
	MEASUREMENT_PERIOD = 0.1
	SPEED_SCALE = 7/MEASUREMENT_PERIOD   # in mm/sec

	def __init__(self):

		# set up motor with PWM and timer control
		self.A1 = Pin('X3',Pin.OUT_PP)	# A is right motor
		self.A2 = Pin('X4',Pin.OUT_PP)
		self.B1 = Pin('X7',Pin.OUT_PP)	# B is left motor
		self.B2 = Pin('X8',Pin.OUT_PP)
		self.PWMA = Pin('X1')
		self.PWMB = Pin('X2')
		self.speed = 0		# +100 full speed forward, -100 full speed back
		self.turn = 0		# turn is +/-100; 0 = left/right same speed,
							# ... +50 = left at speed, right stop, +100 = right back full
		# Configure counter 2 to produce 1kHz clock signal
		self.tim = Timer(2, freq = 1000)
		# Configure timer to provide PWM signal
		self.motorA = self.tim.channel(1, Timer.PWM, pin = self.PWMA)
		self.motorB = self.tim.channel(2, Timer.PWM, pin = self.PWMB)
		self.lsf = 0		# left motor speed factor +/- 1
		self.rsf = 0		# right motor speed factor +/- 1
		self.countA = 0			# speed pulse count for motorA
		self.countB = 0			# speed pulse count for motorB
		self.speedA = 0			# actual speed of motorA
		self.speedB = 0			# actual speed of motorB

		# Create external interrupts for motorA and motorB Hall Effect Senors
		self.motorA_int = pyb.ExtInt ('Y4', pyb.ExtInt.IRQ_RISING, pyb.Pin.PULL_NONE,self.isr_motorA)
		self.motorB_int = pyb.ExtInt ('Y6', pyb.ExtInt.IRQ_RISING, pyb.Pin.PULL_NONE,self.isr_motorB)
		self.speed_timer = pyb.Timer(8, freq=10)
		self.speed_timer.callback(self.isr_speed_timer)

	def isr_motorA(self, line):
		self.countA += 1

	def isr_motorB(self, line):
		self.countB += 1

	def isr_speed_timer(self,t):
		self.speedA = self.countA
		self.speedB = self.countB
		self.countA = 0
		self.countB = 0
		pyb.LED(3).toggle()

	def set_speed(self, value):
		self.speed = value

	def get_speedA(self):
		return self.speedA

	def get_speedB(self):
		return self.speedB

	def set_turn(self, value):
		self.turn = value

	def read_turn(self):
		return self.turn

	def right_forward(self,value):
		self.A2.high()
		self.A1.low()
		self.motorA.pulse_width_percent(abs(value))

	def right_back(self,value):
		self.A2.low()
		self.A1.high()
		self.motorA.pulse_width_percent(abs(value))

	def left_forward(self,value):
		self.B1.high()
		self.B2.low()
		self.motorB.pulse_width_percent(abs(value))

	def left_back(self,value):
		self.B1.low()
		self.B2.high()
		self.motorB.pulse_width_percent(abs(value))

	def stop(self):
		# Motor in idle state
		self.speed = 0
		self.A1.low()
		self.A2.low()
		self.B1.low()
		self.B2.low()
		self.motorA.pulse_width_percent(0)
		self.motorB.pulse_width_percent(0)

	def drive(self):
		DEADZONE = 5
		if (self.speed >= DEADZONE) and (self.turn == 0):		# straight forward
			self.right_forward(self.speed)
			self.left_forward(self.speed)
		elif (self.speed <= -DEADZONE) and (self.turn == 0):	# straight backward
			self.right_back(self.speed)
			self.left_back(self.speed)
		elif (self.speed >= DEADZONE) and (self.turn > 0):		# forward right
			self.lsf = 1		# left wheel speed factor is 1
			self.rsf = 1 - self.turn/50
			self.left_forward(self.speed)

			if (self.rsf > 0):
				self.right_forward(self.rsf*self.speed)
			else:
				self.right_back(self.rsf*self.speed)
		elif (self.speed >= DEADZONE) and (self.turn < 0):		# forward left
			self.rsf = 1		# right wheel speed factor is 1
			self.lsf = 1 + self.turn/50
			self.right_forward(self.rsf*self.speed)
			if (self.lsf > 0):
				self.left_forward(self.lsf*self.speed)
			else:
				self.left_back(self.lsf*self.speed)
		elif (self.speed <= DEADZONE) and (self.turn > 0):		# backward right
			self.rsf = 1		# right wheel speed factor is 1
			self.lsf = 1 - self.turn/50
			self.right_back(self.speed)
			if (self.lsf > 0):
				self.left_back(self.lsf*self.speed)
			else:
				self.left_forward(self.lsf*self.speed)
		elif (self.speed <= DEADZONE) and (self.turn < 0):		# backward left
			self.lsf = 1		# left wheel speed factor is 1
			self.rsf = 1 + self.turn/50
			self.left_back(self.speed)
			if (self.lsf < 0):
				self.right_back(self.rsf*self.speed)
			else:
				self.right_forward(self.rsf*self.speed)
		else:
			self.stop()
