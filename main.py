###############################################################
# Exhaust temperature alarm

###############################################################

from machine import Pin, I2C
from picozero import Button # File needs to be saved on the pico
from ssd1306 import SSD1306_I2C # File needs to be saved on the pico
from oled import Write #, GFX, SSD1306_I2C
from oled.fonts import ubuntu_mono_20
from statemachine import *

BTN_LEFT       = Button(8) # GP8 - pin 11
BTN_RIGHT      = Button(1) # GP1 - pin 2
BTN_ENTER      = Button(5) # GP5 - pin 7

screen_width   = 128
screen_height  = 64

def btn_left_pressed():
    ''' Left button pressed '''
    sm.button_pressed(buttons.LEFT)

def btn_right_pressed():
    ''' Right button pressed '''
    sm.button_pressed(buttons.RIGHT)

def btn_enter_pressed():
    ''' Enter button pressed, sets the state to "menu" '''
    sm.button_pressed(buttons.ENTER)
        
# Start I2C
i2c_dev = I2C(1, scl=Pin(19), sda=Pin(18), freq=200000)
i2c_addr = [hex(ii) for ii in i2c_dev.scan()]  # get I2C address in hex format
if i2c_addr == []:
    print('No I2C Display Found')
    sys.exit()  # exit routine if no dev found
else:
    print("I2C Address      : {}".format(i2c_addr[0]))  # I2C device address
    print("I2C Configuration: {}".format(i2c_dev))  # print I2C params

oled = SSD1306_I2C(screen_width, screen_height, i2c_dev)  # oled controller

# Start the state machine
sm = StateMachine()
sm.add_state(StartState(oled))
sm.add_state(MonitorState(oled))
sm.add_state(MenuState(oled))
sm.go_to_state('start')

# Attach event handlers to the button presses
BTN_LEFT.when_pressed = btn_left_pressed
BTN_ENTER.when_pressed = btn_enter_pressed
BTN_RIGHT.when_pressed = btn_right_pressed
