import pyb
from pyb import Pin, Timer, ADC, DAC, LED, UART
from array import array			# need this for memory allocation to buffers
from oled_938 import OLED_938	# Use OLED display driver
from drive import DRIVE


uart = UART(6)
uart.init(9600, bits=8, parity = None, stop = 2)


def user_move():
    move = "r"
    if uart.any()== 10:
        command = uart.read(10)

        key = command[2]-ord('1')
        pressed = command[3]-ord('1')

        if key == 0:
            move = "q"
        elif key == 1:
            move = "e"
        elif key == 2:
            move = "a"
        elif key == 3:
            move = "d"
        elif key == 4:
            move = "w"
        elif key == 5:
            move = "s"


    return move




            #pressed = command[3]-ord('1')
