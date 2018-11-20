'''
-------------------------------------------------------
Name: microphone
Creator:  Peter Y K Cheung, Imperial College London
Date:   16 March 2017
Revision: 1.0
-------------------------------------------------------
Acquire real-time data from microphone at 8kHz sampling frequency
Find energy in 20msec window

-------------------------------------------------------
'''
import pyb
from pyb import Pin, ADC, Timer

#  The following two lines are needed by micropython
#   ... must include if you use interrupt in your program
import micropython
micropython.alloc_emergency_exception_buf(100)

class MICROPHONE(object):

	def __init__(self, timer, mic, N):

		# initialise variables used for beat detection
		self.count = 0				# sample buffer index pointer
		self.E = 0
		self.sum = 0
		self.finished = False
		self.mic = mic
		self.s = 0
		self.N = N

		# Specify timer 7 interrupt service routine
		timer.callback(self.isr_sampling)

	# Interrupt service routine to fill sample buffer s_buf
	def isr_sampling(self,tim): 	# timer interrupt at 8kHz
		MIC_OFFSET = 1523		# ADC reading of microphone for silence
		self.s = self.mic.read() - MIC_OFFSET  # read one sample and remove dc offset
		self.count = self.count	+ 1	# increment sample count
		self.sum = self.sum + self.s*self.s
		if (self.count == self.N):	# when reach N
			self.count = 0
			self.E = self.sum
			self.sum = 0
			self.finished = True	# set the flag (semaphore) for buffer full

	def buffer_full(self):
		return self.finished

	def set_buffer_empty(self):
		self.finished = False

	def inst_energy(self):
		return self.E

		
