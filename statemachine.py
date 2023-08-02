
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
    
# The state machine class keeps track of possible states,
# and which state is currently active.
class StateMachine(object):

    def __init__(self):
        self.state = None
        self.states = {}
        
    def add_state(self, state):
        self.states[state.name] = state

    def go_to_state(self, state_name):
        if self.state:
            #log('Exiting %s' % (self.state.name))
            self.state.exit(self)
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

    def __init__(self, oled):
        self.oled = oled

    @property
    def name(self):
        return ''

    # These are the methods that will be called on each state
    def enter(self, machine):
        pass

    def exit(self, machine):
        pass

    def update(self, machine):
        return True

    def button_pressed(self, machine, button):
        pass

class StartState(State):
    
        @property
        def name(self):
            return "start"
        
        def enter(self, machine):
            State.enter(self, machine)
            
            self.oled.fill(0)
            self.oled.show()

            self.oled.rect(0, 0, self.oled.width, self.oled.height, 1)
            self.oled.text("Exhaust", 37, 10)
            self.oled.text("temperature", 20, 20)
            self.oled.text("alarm", 43, 30)
            self.oled.text("Version {}".format(0.5), 28, 45)
            self.oled.show()

            sleep(2)
            machine.go_to_state('monitor')
        
        def exit(self, machine):
            self.oled.fill(0)
            self.oled.show()
        
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

    BUZZER         = None

    timer          = Timer(-1)
    counter        = 0
    history        = []               # 128 measurements
    silent         = False         # Alarm is silent
    alarm          = False            # Alarm is on

    def __init__(self, oled):
        super().__init__(oled)

        self.TEMP_SENSOR = machine.ADC(26)  # Channel 0
        self.OFFSET_SENSOR = machine.ADC(27)  # Channel 1
        self.BUZZER = Pin(14, Pin.OUT)  # Buzzer pin

    @property
    def name(self):
        return "monitor"
    
    def enter(self, machine):
        State.enter(self, machine)
        
        ''' Start the timer that calls the update routine at set intervals '''
        self.timer.init(period=self.UPDATE_TIME_MS, mode=Timer.PERIODIC, callback=self.update)
        
        # Test the buzzer
        self.sound_buzzer()
    
    def exit(self, machine):
        self.timer.deinit()
        self.counter = 0
    
    def update(self, machine):
        # Clear all
        self.oled.fill(0)

        # Make the measurement
        measurement = self.TEMP_SENSOR.read_u16() - self.adc_offset
        voltage = (measurement * (self.ADC_REF_VOLT)) / 65535
        temp_celsius = voltage / (10.0 / 1000)

        # Record a history point every n seconds
        if self.counter % self.HIST_INTERVAL == 0:
            self.history.append(temp_celsius)

            if len(self.history) == 128:
                self.history.pop(0)  # remove first element

        # Display the value
        write20 = Write(self.oled, ubuntu_mono_20)
        if temp_celsius >= self.ALARM_TEMP:
            self.alarm = True
            write20.text("!!! {:.0f}C !!!".format(temp_celsius), 10, 0)
            self.sound_buzzer()

        else:
            self.alarm = False
            self.silent = False
            write20.text("{:.0f}C".format(temp_celsius), 50, 0)

        # Display the graph
        scaler = 44 / self.MAX_TEMP  # Scale 0-150 degrees to 0-44 available pixels => 0.2933
        self.oled.rect(0, 20, self.oled.width, self.oled.height - 20, 1)  # rect around graph

        # dotted line at alarm temperature
        for x in range(self.oled.width):
            if x % 4 == 0:
                self.oled.pixel(x, self.oled.height - int(self.ALARM_TEMP * scaler), 1)

        # historical temperature
        for x in range(len(self.history)):
            self.oled.pixel(x, self.oled.height - int(self.history[x] * scaler), 1)

        # Show it all
        self.oled.show()

        self.counter = self.counter + 1
    
    def sound_buzzer(self):
        if self.silent == False:
            for x in range(4):
                self.BUZZER.high()
                sleep(0.1)
                self.BUZZER.low()
                sleep(0.1)

                if self.silent == True:
                    continue

    def button_pressed(self, machine, button):
        
        if self.alarm == True:
            # If alarm is on, silence it
            self.silent = True

        else:
            # No alarm, just handle the button event
            if button == buttons.ENTER:
                machine.go_to_state('menu')

class MenuState(State):

    @property
    def name(self):
        return "menu"
    
    def enter(self, machine):
        State.enter(self, machine)

        self.oled.fill(0)
        self.oled.text(self.name, 0, 0)
        self.oled.show()

    def button_pressed(self, machine, button):
        if button == buttons.ENTER:
            machine.go_to_state('monitor')
        
