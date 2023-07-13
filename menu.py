
class Menu():

    oled = None	
    menu = ["Settings", "Info"]
    line = 1
    line_height = 10

    def __init__(self):
        pass

    def display_menu(self):
        for item in self.menu:
            self.oled.text(item, 10, self.line * self.line_height)

