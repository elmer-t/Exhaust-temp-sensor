
# https://learn.adafruit.com/circuitpython-101-state-machines?view=all


from utime import sleep
from machine import Timer, Pin
from oled import Write  # , GFX, SSD1306_I2C
from oled.fonts import ubuntu_mono_20
import machine

class buttons():
    ENTER = 1
    LEFT = 2
    RIGHT = 3

# The hardware class keeps track of all the hardware components
# It represents the Pico, buzzer, SSD1306 oled display and buttons
class Hardware(object):

    BUZZER         = None

    silent         = False            # Alarm is silent

    def __init__(self, oled):
        self.oled = oled
        self.buttons = None
        self.BUZZER = Pin(14, Pin.OUT)  # Buzzer pin
        
        print('Hardware initialized')

    def sound_buzzer(self):
        print('Sounding buzzer...')

        if self.silent == False:
            for x in range(4):
                self.BUZZER.high()
                sleep(0.1)
                self.BUZZER.low()
                sleep(0.1)

                if self.silent == True:
                    continue

# The state machine class keeps track of possible states,
# and which state is currently active.
class StateMachine(object):

    #state = None
    #states = {}
    #hardware = None
    
    def __init__(self, hardware):
        self.state = None
        self.hardware = hardware
        self.states = {}
        
        print('State machine initialized')
        
    def add_state(self, state):
        print('Adding "%s" state...' % state.name)
        self.states[state.name] = state
        print('Added "%s" state' % state.name)

    def go_to_state(self, state_name):
        print('Going to "%s" state...' % state_name)
        
        if self.state:
            #log('Exiting %s' % (self.state.name))
            self.state.exit(self)
        
        # check if self.states contains the state_name
        if state_name not in self.states:
            print('State "%s" not found' % state_name)
            return
        
        self.state = self.states[state_name]
        #log('Entering %s' % (self.state.name))
        self.state.enter(self)

    def update(self):
        if self.state:
            self.state.update(self)

    def button_pressed(self, button):
        if self.state:
            self.state.button_pressed(self, button)


# Base class for all states
class State(object):
    
    oled = None

    def __init__(self):
        pass

    @property
    def name(self):
        return ''

    # These are the methods that will be called on each state
    def enter(self, sm):
        print('Entering "%s" state' % self.name)
        pass

    def exit(self, sm):
        print('Exiting "%s" state' % self.name)
        pass

    def update(self, sm):
        print('Updating "%s" state' % self.name)
        return True

    def button_pressed(self, sm, button):
        print('Button "%s" pressed' % button)
        pass

class StartState(State):
    
        @property
        def name(self):
            return "start"
        
        def enter(self, sm):
            State.enter(self, sm)
            
            sm.hardware.oled.fill(0)
            sm.hardware.oled.show()

            sm.hardware.oled.rect(0, 0, sm.hardware.oled.width, sm.hardware.oled.height, 1)
            sm.hardware.oled.text("Exhaust", 37, 10)
            sm.hardware.oled.text("temperature", 20, 20)
            sm.hardware.oled.text("alarm", 43, 30)
            sm.hardware.oled.text("Version {}".format(0.6), 20, 45)
            sm.hardware.oled.show()

            # Test the buzzer
            sm.hardware.sound_buzzer()
            
            sleep(2)
            sm.go_to_state('monitor')
        
        def exit(self, sm):
            sm.hardware.oled.fill(0)
            sm.hardware.oled.show()
        
class MonitorState(State):

    UPDATE_TIME_MS = const(1000)      # every second

    TEMP_SENSOR    = None
    OFFSET_SENSOR  = None
    ADC_REF_VOLT   = 3.3              # Should be 3.3 which is the ref for the ADC, not the 5V VBUS that powers the LM35
    adc_offset     = 0                # Initialize to zero
    HIST_INTERVAL  = const(7)         # A history point every 7 seconds, giving about 15 minutes graph
    ALARM_TEMP     = 30               # Alarm temperature, 65 degrees Celsius
    MIN_TEMP       = const(0)
    MAX_TEMP       = const(150)

    timer          = Timer(-1)
    counter        = 0
    history        = []               # 128 measurements
    alarm          = False            # Alarm is on

    def __init__(self):
        self.TEMP_SENSOR = machine.ADC(26)  # Channel 0
        self.OFFSET_SENSOR = machine.ADC(27)  # Channel 1

    @property
    def name(self):
        return "monitor"
    
    def enter(self, sm):
        State.enter(self, sm)
        
        ''' Start the timer that calls the update routine at set intervals '''
        # make a lambda so I can pass sm as a parameter to the timer callback
        my_callback = lambda timer: self.update(sm)
        
        self.timer.init(period=self.UPDATE_TIME_MS, mode=Timer.PERIODIC, callback=my_callback)
            
    def exit(self, sm):
        self.timer.deinit()
        self.counter = 0
    
    def update(self, sm):
        print('Updating "%s" state' % self.name)
        # Clear all
        sm.hardware.oled.fill(0)
        
        # Make the measurement
        measurement = self.TEMP_SENSOR.read_u16() - self.adc_offset
        voltage = (measurement * (self.ADC_REF_VOLT)) / 65535
        temp_celsius = voltage / (10.0 / 1000)
        print("Temperature: {:.0f}C".format(temp_celsius))

        # Record a history point every n seconds
        if self.counter % self.HIST_INTERVAL == 0:
            self.history.append(temp_celsius)

            if len(self.history) == 128:
                self.history.pop(0)  # remove first element

        # Display the value
        write20 = Write(sm.hardware.oled, ubuntu_mono_20)
        if temp_celsius >= self.ALARM_TEMP:
            self.alarm = True
            write20.text("!!! {:.0f}C !!!".format(temp_celsius), 10, 0)
            sm.hardware.sound_buzzer()

        else:
            self.alarm = False
            sm.hardware.silent = False
            write20.text("{:.0f}C".format(temp_celsius), 50, 0)

        # Display the graph
        scaler = 44 / self.MAX_TEMP  # Scale 0-150 degrees to 0-44 available pixels => 0.2933
        sm.hardware.oled.rect(0, 20, sm.hardware.oled.width, sm.hardware.oled.height - 20, 1)  # rect around graph

        # dotted line at alarm temperature
        for x in range(sm.hardware.oled.width):
            if x % 4 == 0:
                sm.hardware.oled.pixel(x, sm.hardware.oled.height - int(self.ALARM_TEMP * scaler), 1)

        # historical temperature
        for x in range(len(self.history)):
            sm.hardware.oled.pixel(x, sm.hardware.oled.height - int(self.history[x] * scaler), 1)

        # Show it all
        sm.hardware.oled.show()
        
        self.counter = self.counter + 1
    
    def button_pressed(self, machine, button):
        
        if self.alarm == True:
            # If alarm is on, silence it
            self.silent = True

        else:
            # No alarm, just handle the button event
            if button == buttons.ENTER:
                machine.go_to_state('menu')

class MenuState(State):

    menu = [
        "Alarm temp %sC" % MonitorState.ALARM_TEMP, 
        "Graph time %ss" % (MonitorState.HIST_INTERVAL * MonitorState.UPDATE_TIME_MS / 1000),
        "Info",
        "Exit"
    ]
    selected_line = 1 # the currently selected line in the menu
    line_height = 10

    @property
    def name(self):
        return "menu"
    
    def enter(self, sm):
        State.enter(self, sm)
        self._display_menu(sm)

    def button_pressed(self, sm, button):
        if button == buttons.ENTER:
            sm.go_to_state('monitor')

        elif button == buttons.LEFT:
            self.selected_line = self.selected_line - 1
            if self.selected_line < 1:
                self.selected_line = len(self.menu)
            self._display_menu(sm)

        elif button == buttons.RIGHT:
            self.selected_line = self.selected_line + 1
            if self.selected_line > len(self.menu):
                self.selected_line = 1
            self._display_menu(sm)
            
    def _display_menu(self, sm):
        sm.hardware.oled.fill(0) # clear the screen

        pix_res_x = const(128)
        pix_res_y = const(64)

        # iterate over menu items with item and index
        for index, item in enumerate(self.menu):
            
            # invert the currently selected item
            if index == self.selected_line - 1:
                sm.hardware.oled.fill_rect(0, index * self.line_height, pix_res_x, self.line_height, 1)
                sm.hardware.oled.text(item, 10, index * self.line_height, 0)
            else:
                sm.hardware.oled.text(item, 10, index * self.line_height)

        sm.hardware.oled.show()
