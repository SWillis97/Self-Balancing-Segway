import pyb
from pyb import LED, Pin, Timer, Switch
from oled_938 import OLED_938
from mpu6050 import MPU6050


def init_motors():
    A1 = Pin('X3', Pin.OUT_PP)
    A2 = Pin('X4', Pin.OUT_PP)
    PWMA = Pin('X1')

    B1 = Pin('X7', Pin.OUT_PP)
    B2 = Pin('X8', Pin.OUT_PP)
    PWMB = Pin('X2')

    tim = Timer(2, freq=1000)
    motorA = tim.channel(1, Timer.PWM, pin=PWMA)
    motorB = tim.channel(2, Timer.PWM, pin=PWMB)
    return A1, A2, B1, B2, motorA, motorB


def init_oled():
    # I2C connected to Y9, Y10 (I2C bus 2) and Y11 is reset low active
    #OLED
    oled = OLED_938(pinout={'sda': 'Y10', 'scl': 'Y9', 'res': 'Y8'}, height=64,
                       external_vcc=False, i2c_devid=61)
    oled.poweron()
    oled.init_display()
    oled.draw_text(0,20,"Initializing Oled...")
    oled.display()
    return oled

def init_PWM():
    tim = Timer(2, freq=1000)

def initalize_robot():
    oled = init_oled()
    pot = pyb.ADC(Pin('X11'))

    A1, A2, B1, B2, motorA, motorB = init_motors()

    # Define LEDs
    b_LED = LED(4)
    b_LED.toggle()
    # IMU connected to X9 and X10
    imu = MPU6050(1, False)    	 # Use I2C port 1 on Pyboard
    oled.draw_text(0,40,"Initializing Robot...")
    oled.display()
    return imu, oled, pot, A1, A2, B1, B2, motorA, motorB
