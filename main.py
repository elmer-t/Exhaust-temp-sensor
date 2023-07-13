###############################################################
# Exhaust temperature alarm

###############################################################

from machine import Pin, I2C, Timer
from picozero import Button # File needs to be saved on the pico
from ssd1306 import SSD1306_I2C # File needs to be saved on the pico
from oled import Write #, GFX, SSD1306_I2C
from oled.fonts import ubuntu_mono_20

from utime import sleep
import sys
from statemachine import *

VERSION        = const(0.3)       # Script version
pix_res_x      = const(128)       # SSD1306 horizontal resolution
pix_res_y      = const(64)        # SSD1306 vertical resolution
UPDATE_TIME_MS = const(1000)      # every second
BUZZER         = Pin(14, Pin.OUT) # Buzzer pin
TEMP_SENSOR    = machine.ADC(26)  # Channel 0
OFFSET_SENSOR  = machine.ADC(27)  # Channel 1
ADC_REF_VOLT   = 3.3              # Should be 3.3 which is the ref for the ADC, not the 5V VBUS that powers the LM35
adc_offset     = 0                # Initialize to zero
ALARM_TEMP     = 65
MIN_TEMP       = const(0)
MAX_TEMP       = const(150)
HIST_INTERVAL  = const(7)         # A history point every 7 seconds, giving about 15 minutes graph

BTN_LEFT       = Button(8) # GP8 - pin 11
BTN_RIGHT      = Button(1) # GP1 - pin 2
BTN_ENTER      = Button(5) # GP5 - pin 7

history = [] # 128 measurements
counter = 0
timer = Timer(-1)

class Menu():

    menu = [
        "Alarm temp", 
        "Graph time",
        "Info",
        "Exit"
    ]
    selected_line = 1 # the currently selected line in the menu
    line_height = 10

    def __init__(self):
        pass

    def _display_menu(self):
        cls()

        # iterate over menu items with item and index
        for index, item in enumerate(self.menu):
            
            # invert the currently selected item
            if index == self.selected_line - 1:
                oled.fill_rect(0, index * self.line_height, pix_res_x, self.line_height, 1)
                oled.text(item, 10, index * self.line_height, 0)
            else:
                oled.text(item, 10, index * self.line_height)

        oled.show()

    def btn_left(self):
        self.selected_line = self.selected_line - 1
        if self.selected_line < 1:
            self.selected_line = len(self.menu)
        self._display_menu()

    def btn_right(self):
        self.selected_line = self.selected_line + 1
        if self.selected_line > len(self.menu):
            self.selected_line = 1
        self._display_menu()

    def btn_enter(self):
        cls()

        # get the selected menu item from the menu dictionary
        oled.text(self.menu[self.selected_line-1], 30, 0)
        oled.show()
        

def update(timer):
    ''' The main update routine '''
    global history
    global counter
    
    # Clear all
    oled.fill(0)

    # Make the measurement
    measurement = TEMP_SENSOR.read_u16() - adc_offset
    voltage = (measurement * (ADC_REF_VOLT)) / 65535
    temp_celsius =  voltage / (10.0 / 1000)
    
    # Record a history point every n seconds
    if counter % HIST_INTERVAL == 0:
        history.append(temp_celsius)
        
        if len(history) == 128:
            history.pop(0) # remove first element
            
    # Display the value
    write20 = Write(oled, ubuntu_mono_20)
    if temp_celsius >= ALARM_TEMP:
        write20.text("!!! {:.0f}C !!!".format(temp_celsius), 10, 0)
        alarm()
    else:
        write20.text("{:.0f}C".format(temp_celsius), 50, 0)
    
    # Display the graph
    scaler = 44 / MAX_TEMP # Scale 0-150 degrees to 0-44 available pixels => 0.2933
    oled.rect(0, 20, pix_res_x, pix_res_y-20, 1) # rect around graph

    # dotted line at alarm temperature
    for x in range(pix_res_x):
        if x % 4 == 0:
            oled.pixel(x, pix_res_y - int(ALARM_TEMP * scaler), 1) 
    
    # historical temperature
    for x in range(len(history)):
        oled.pixel(x, pix_res_y - int(history[x] * scaler), 1)
    
    # Show it all
    oled.show();

    counter = counter +1

def debug(timer):
    ''' Show some debug values '''
    oled.fill(0)

    measurement = TEMP_SENSOR.read_u16() - adc_offset
    voltage = (measurement * (ADC_REF_VOLT)) / 65535
    temp_celsius =  voltage / (10.0 / 1000)

    oled.text("ADC   : {0}".format(measurement), 0, 0)
    oled.text("Offset: {0}".format(adc_offset), 0, 10)
    oled.text("Volt  : {:.0f}mV".format(voltage * 1000), 0, 20)
    oled.text("Temp  : {:.1f}*C".format(temp_celsius), 0, 30)
    
    vsys_channel = machine.ADC(29)
    vsys_value = vsys_channel.read_u16()
    vsys_voltage = (vsys_value * ADC_REF_VOLT / 65535) * 3
    oled.text("VSYS  : {:.2f}V".format(vsys_voltage), 0, 40)
    
    oled.show()

def set_adc_offset():
    ''' # Sets the ADC offset (0-65535) based on the voltage '''
    ''' measured on ADC1, which is connected to GND. '''
    global adc_offset
    adc_offset = OFFSET_SENSOR.read_u16() # 0-65535
    #adc_offset = (measurement * ADC_REF_VOLT) / 65535
    
def startup_screen():
    ''' Briefly show startup screen '''
    oled.rect(0, 0, pix_res_x, pix_res_y, 1)
    oled.text("Exhaust", 37, 10)
    oled.text("temperature", 20, 20)
    oled.text("alarm", 43, 30)
    oled.text("Version {}".format(VERSION), 28, 45)
    oled.show()

def alarm():
    ''' Test the buzzer by giving a few short beeps '''
    for x in range(4):
        BUZZER.high()
        sleep(0.1)
        BUZZER.low()
        sleep(0.1)
        
def cls():
    ''' Clear the screen '''
    oled.fill(0)
    oled.show()

def start_timer():
    ''' Start the timer that calls the update routine at set intervals '''
    timer.init(period=UPDATE_TIME_MS, mode=Timer.PERIODIC, callback=update)
    
def stop_timer():
    ''' Stop the timer '''
    timer.deinit()

def btn_left_pressed():
    ''' Left button pressed '''
    #stop_timer()
    sm.button_pressed(buttons.LEFT)

def btn_right_pressed():
    ''' Right button pressed '''
    #stop_timer()
    sm.button_pressed(buttons.RIGHT)

def btn_enter_pressed():
    ''' Enter button pressed, sets the state to "menu" '''
    #stop_timer()
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

oled = SSD1306_I2C(pix_res_x, pix_res_y, i2c_dev)  # oled controller
cls()

sm = StateMachine()
sm.add_state(MonitorState(oled))
sm.add_state(MenuState())
sm.go_to_state('monitor')

BTN_LEFT.when_pressed = btn_left_pressed
BTN_ENTER.when_pressed = btn_enter_pressed
BTN_RIGHT.when_pressed = btn_right_pressed

#menu = Menu()  # Global menu object
#menu.oled = oled

#startup_screen() # Show startup screen for a few moments
#alarm()          # Test alarm once
#set_adc_offset() # Measure offset to compensate pico variations
#sleep(1)         # Wait a second...
#cls()            # Clear the screen
#start_timer()    # Main routine - measures temperature at set intervals



