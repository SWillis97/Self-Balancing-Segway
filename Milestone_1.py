import pyb
from pyb import Pin, Timer, ADC, DAC, LED, UART
from array import array			# need this for memory allocation to buffers
from oled_938 import OLED_938	# Use OLED display driver
from drive import DRIVE


uart = UART(6)
uart.init(9600, bits=8, parity = None, stop = 2)
#motor = DRIVE()
speed = 60

A1 = Pin ('X3', Pin.OUT_PP)   # Control direction of motor A
A2 = Pin('X4', Pin.OUT_PP)
PWMA = Pin('X1')              # Control speed of motor A
B1 = Pin ('X7', Pin.OUT_PP)   # Control direction of motor B
B2 = Pin('X8', Pin.OUT_PP)
PWMB = Pin('X2')              # Control speed of motor B

# Configure timer 2 to produce 1KHz clock for PWM Controltim = Timer(2, freq = 1000)
tim = Timer(2, freq = 1000)
motorA = tim.channel(1, Timer.PWM, pin = PWMA)
motorB = tim.channel(2, Timer.PWM, pin = PWMB)

def A_forward(value):
    A1.low()
    A2.high()
    motorA.pulse_width_percent(value)

def A_back(value):
    A1.high()
    A2.low()
    motorA.pulse_width_percent(value)

def A_stop():
    A1.high()
    A2.high()

def B_forward(value):
    B2.low()
    B1.high()
    motorB.pulse_width_percent(value)

def B_back(value):
    B2.high()
    B1.low()
    motorB.pulse_width_percent(value)

def B_stop():
    B1.high()
    B2.high()


while True:
    while (uart.any()!=10):
        n = uart.any()
        command = uart.read(10)
        print(command)
        if command != None:
            key = command[2]-ord('1')
            pressed = command[3]-ord('1')

            if pressed == 0:
                if key == 4:
                    A_forward(speed)
                    B_forward(speed)
                elif key == 5:
                    A_back(speed/2)
                    B_back(speed/2)
                elif key == 7:
                    A_back(speed/2)
                    B_forward(speed/2)
                elif key == 6:
                    A_forward(speed/2)
                    B_back(speed/2)
                elif key == 0:
                    A_stop()
                    B_stop()
            else:
                A_stop()
                B_stop()
