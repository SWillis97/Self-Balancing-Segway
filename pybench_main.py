import pyb
import gc
from pyb import LED, USB_VCP, LED
from array import array
from pybench import PYBENCH
from struct import unpack

u = pyb.USB_VCP()

r_LED = LED(1)
g_LED = LED(2)
y_LED = LED(3)
b_LED = LED(4)
y_LED.off()

g = PYBENCH(pins={'a_out': 'X5', 'a_in': 'X12', 'mic': 'Y11', 'pot': 'X11'})
ack = bytearray(1)
ack[0] = 33
s_buffer = bytearray(2)

def write_one(sample):
	buf = bytearray(2)
	buf[0] = sample >> 8
	buf[1] = sample % 256
	u.write(buf)
	
def write_block(s_buf):
	nsamp = len(s_buf)
	buf = bytearray(nsamp*2)
	for i in range (nsamp):
		buf[2*i] = s_buf[i] >> 8
		buf[2*i+1] = s_buf[i] % 256
	u.send(buf)
	
def done():
	u.send(ack)

while True:
	try:
		s = ''
		b_LED.on()
		while not s or s[-1] != '\n':
			char = u.read(1)
			if char:
				s += char.decode('utf-8')
		s = s[:-1]
		b_LED.off()
		g_LED.off()
		value = 0
		command = s[0]

		if(len(s)>=2):
			value = int(s[1:len(s)])	

		if (command == 'V'):
			g.put(value)
			done()
		elif (command == 'B'):
			sample = g.get()
			write_one(sample)
			g.out(value)
		elif (command == 'S'):
			g.put_sine()
			done()
		elif (command == 'F'):
			g.set_sig_freq(value)
			done()
		elif (command == 'A'):
			g.set_samp_freq(value)
			done()
		elif (command == 'X'):
			g.set_max_v(value)
			done()
		elif (command == 'N'):
			g.set_min_v(value)
			done()
		elif (command == 'D'):
			g.set_duty_cycle(value)
			done()
		elif (command == 'W'):
			g.set_N_window(value)
			done()
		elif (command == 'Q'):
			g.put_square()
			done()
		elif (command == 'T'):
			g.put_triangle()
			done()
		elif (command == 'G'):
			sample = g.get()
			write_one(sample)
		elif (command == 'U'): 
			sample = g.get_mean(value)
			m = "Sample: %4.2fV" % (sample*3.3/4096)
			g.write_message(m)
			write_one(sample)
		elif (command == 'M'):
			g_LED.on()
			s_buf = g.get_block(value)
			write_block(s_buf)
			g_LED.off()
			gc.collect()
		elif (command == 'J'):
			g_LED.on()
			s_buf = g.get_mic(value)
			write_block(s_buf)
			g_LED.off()
			gc.collect()
		elif (command == 'I'):
			g_LED.on()
			[accel, gyro] = g.get_imu()
			u.send(accel)
			u.send(gyro)
			g_LED.off()
		elif (command == 'K'):
			g_LED.on()
			accel = g.get_accel()
			u.send(accel)
			g_LED.off()
		elif (command == 'L'):
			g_LED.on()
			gyro = g.get_gyro()
			u.send(gyro)
			g_LED.off()
# Motor interaction commands C, E, Y, Z added for version 1.2 on 3 March 2017			
		elif (command == 'C'):
			g.control_motor_speed(value)
			done()
		elif (command == 'E'):
			g.set_motor_direction(value)
			done()
		elif (command == 'Y'):
			g.set_motor_speed(value)
			done()
		elif (command == 'Z'):
			g_LED.on()
			speed_buf = g.get_motor_speed()
			u.send(speed_buf)
			g_LED.off()
		elif (command == '?'):
			pyb.delay(100)
			done()
	except ValueError:
		pass
 