
# https://learn.adafruit.com/circuitpython-101-state-machines?view=all

class buttons():
    ENTER = 1
    LEFT = 2
    RIGHT = 3
    
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
            #log('Updating %s' % (self.state.name))
            self.state.update(self)

    def button_pressed(self, button):
        if self.state:
            #log('Button Left Pressed %s' % (self.state.name))
            self.state.button_pressed(self, button)

# Base class for all states
class State(object):
    
    def __init__(self):
        pass

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

class MonitorState(State):

    oled = None

    def __init__(self, oled):
        self.oled = oled

    @property
    def name(self):
        return "monitor"
    
    def enter(self, machine):
        State.enter(self, machine)
        
        self.oled.text(self.name, 0, 0)
        self.oled.show()
    
    def button_pressed(self, machine, button):
        if button == buttons.ENTER:
            machine.go_to_state('menu')

        #State.button_pressed(self, machine)

    
class MenuState(State):

    def __init__(self):
        pass

    @property
    def name(self):
        return "menu"
    
    def enter(self, machine):
        State.enter(self, machine)

        oled.text(self.name, 0, 0)
        oled.show()

    def button_pressed(self, machine, button):
        if button == buttons.ENTER:
            machine.go_to_state('monitor')
        
