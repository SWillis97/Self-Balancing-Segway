'''
-------------------------------------------------------
Name: main
Creator:  Peter Y K Cheung, Imperial College London
Date:   2 Jan 2017
Revision: 1.0
-------------------------------------------------------
This is the main program for DE2 Lab environment.  On power up,
SW1:0 is read and determines the action taken:

SW=00  Run pybench.py    	run the PyBench environment
SW=11  Run pybench_test.py  run the self-test programme

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
from pyb import Pin, LED

#  Configure X2:4, X7 as setting input pin - pull_up to receive switch settings
s0=Pin('Y3',pyb.Pin.IN,pyb.Pin.PULL_UP)
s1=Pin('X6',pyb.Pin.IN,pyb.Pin.PULL_UP)
r_LED = LED(1)
g_LED = LED(2)
y_LED = LED(3)
b_LED = LED(4)
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

if read_sw() == 0:
	print('Running PyBench')
	execfile('master.py')	 # for self balance Driving
elif read_sw() == 1:
	print('Running PyBench Selftest')
	execfile('pybench_test.py')
elif read_sw() == 2:
	print('Running PyBench Selftest')
	execfile('pybench_test.py')
elif read_sw() == 3:
	print('Running User Python Program')
	execfile('Flash_PID.py') # for self balance Dancing
