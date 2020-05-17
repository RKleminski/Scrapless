import tkinter as tk
import tkinter.font as tkfont

from win32 import win32gui
from math import ceil

import win32con

'''
A class that renders, manages and stores app overlay
Initialised using parametres read from config files
Intended to be used as a part of text output to user
'''
class Overlay:

    def __init__(self, init_line, opacity, pos_x, pos_y, max_lines, font, font_size, colors):
        
        # parametres to keep in the class
        self.max_lines = max_lines
        self.font = (font, font_size)
        self.colors = colors

        self.root = self._setRoot(pos_x, pos_y, opacity, init_line)
        self.display = []

        self.writeLine(init_line, 'info')

    '''
    A function to prepare the overlay for operation
    Returns the root element
    '''
    def _setRoot(self, pos_x, pos_y, opacity, init_line):

        root = tk.Tk()
        root.title(init_line)

        # configure the overlay widget, aka the master widget of the line we have created
        root.overrideredirect(True)                  # this prevents the override from behaving like a regular window
        root.geometry(f'+{pos_x}+{pos_y}')           # this sets overlay's initial position
        root.minsize(500, 20)                        # set minimum widget size to max of what it will ever be
        root.configure(bg=self.colors['background']) # set the BG colour of the widget
        root.wm_attributes('-topmost', True)         # make sure the overlay widget stays on top of other windows
        root.wm_attributes('-alpha', opacity)        # set opacity to make the widget semi-transparent

        root.update()

        # set the window to allow clicking events to go through
        window = win32gui.FindWindow(None, init_line)                    # find our window to edit it
        lExStyle = win32gui.GetWindowLong(window, win32con.GWL_EXSTYLE)
        lExStyle |=  win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
        win32gui.SetWindowLong(window, win32con.GWL_EXSTYLE , lExStyle )

        return root

    '''
    A function for writing a new line to the overlay
    In a specified
    '''
    def writeLine(self, text_line, line_color):

        # if the overlay is already at max display capacity,
        # keep trimming it until that is fixed
        while len(self.display) >= self.max_lines:

            # destroy the label object
            self.display[0].destroy()

            # remove the object from the array
            self.display.pop(0)

        # create new text label, aka a line in the overlay
        label = tk.Label(text=text_line, font=self.font, fg=self.colors[line_color], bg=self.colors['background'])

        # add the newly created line to the overlay
        self.display.append(label)

        # cook the line into the widget
        label.pack()

        # update overlay and ensure it stays on top
        self.root.update()
        self.root.lift()

        # a bit hamfisted way to ensure overlay starts in its full size
        # for aesthetic reasons
        if len(self.display) == 1:
            self.root.minsize(500, self.max_lines*label.winfo_height())
            self.root.update()

    '''
    A function for refreshing the current state of the overlay
    This is very important, as the overlay will stop responding if
    not refreshed for a while
    '''
    def refresh(self):

        # refresh the master widget
        self.root.update()

        # lift the overlay to top
        self.root.lift()