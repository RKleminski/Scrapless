from configurable import Configurable
from win32 import win32gui
from math import ceil

import tkinter as tk
import tkinter.font as tkfont

import re
import win32.lib.win32con as win32con

'''
A class that renders, manages and stores app overlay
Inherits after Configurable
Initialised using parametres read from config files
Intended to be used as a part of text output to user
'''
class Overlay(Configurable):

    #
    # CLASS VARIABLES
    #
    # path to config file
    OVR_PATH = './data/json/config/overlay.json'

    def __init__(self, init_line):

        # invoke the parent initialisation method
        Configurable.__init__(self, self.OVR_PATH)

        # read whether the overlay is to be enabled
        self.enabled = self._setEnabled()

        if self.enabled:
            
            # read parametres from the config file
            self.opacity = self._setOpacity()
            self.position = self._setPosition()
            self.max_lines = self._setMaxLines()
            self.font = self._setFont()
            self.colors = self._setColors()

            self.root = self._setRoot(init_line)
            self.display = []

            self.writeLine(init_line, 'info')

    '''
    Method for loading enabled value
    Expected value is a string of either yes or no, case insensitive
    Raises an exception if unexpected value is met
    '''
    def _setEnabled(self):

        # read the key value first
        enabled = self.readKey('enable').lower()

        # check if the value is a string
        if type(enabled) == str:

            # check if the value is legal
            if enabled in ['yes', 'no']:

                # convert to a boolean and return
                return enabled == 'yes'

            # otherwise raise an exception
            raise ValueError(f'"enable" must be either a "Yes" or "No", case insensitive; in {self.conf_path}')

        # otherwise raise an exception
        raise TypeError(f'"enable" has to be a string; in {self.conf_path}')

    '''
    Method for loading opacity value
    Expected value is an integer greater than zero
    Raises an exception if unexpected value is met
    '''
    def _setOpacity(self):

        # read the key value first
        opacity = self.readKey('opacity')

        # check if value is an integer
        if type(opacity) == int:

            # check if the value is greater than 0
            if opacity > 0:

                # convert to appropriate float and return
                return opacity / 100.0
            
            # raise an exception otherwise
            raise ValueError(f'"opacity" value must be greater than 0; in {self.conf_path}')

        # raise an exception otherwise
        raise TypeError(f'"opacity" has to be an integer; in {self.conf_path}')

    '''
    Method for reading overlay position on the screen
    Expected value is a dictionary with two values
    Returns a dictionary
    Raises an exception if dictionary is not up to spec
    '''
    def _setPosition(self):

        # start with reading the key
        position = self.readKey('position')

        # check if dictionary is of expected length
        if len(position) == 2:

            # check if both coordinates are aptly named
            if all(key in position.keys() for key in ['X', 'Y']):

                # check value types
                if type(position['X']) == int and type(position['Y']) == int:

                    # return the dict
                    return position

                # otherwise raise an exception
                raise TypeError(f'"position" coordinates "X" and "Y" have to be integers; in {self.conf_path}')

            # otherwise raise an exception
            raise KeyError(f'"position" specification should contain "X" and "Y" field, case sensitive; in {self.conf_path}')

        # otherwise raise an exception
        raise ValueError(f'"position" expected to contain exactly two coordinates; in {self.conf_path}')

    '''
    Method for loading max_lines value
    Expected value is an integer greater than zero
    Raises an exception if unexpected value is met
    '''
    def _setMaxLines(self):

        # read the key value first
        max_lines = self.readKey('max_lines')

        # check if value is an integer
        if type(max_lines) == int:

            # check if the value is greater than 0
            if max_lines > 0:

                # convert to appropriate float and return
                return max_lines
            
            # raise an exception otherwise
            raise ValueError(f'"max_lines" value must be greater than 0; in {self.conf_path}')

        # raise an exception otherwise
        raise TypeError(f'"max_lines" has to be an integer; in {self.conf_path}')

    '''
    Method for loading font specifications
    Expected value is a string name of a font and numerical font size
    Returns a font tuple compatible with TKinter
    Raises an exception if unexpected value is met
    '''
    def _setFont(self):

        # temporary TK instance to access fonts
        # hacky, but there is no other way than to download a whole list
        temp_tk = tk.Tk()

        # read the key value first
        font_dict = self.readKey('font')

        # check if font type is present
        if 'font-name' in font_dict.keys():

            # get the font name
            font_name = font_dict['font-name']

            # check if font-name is a string
            if type(font_name) == str:

                # raise an exception if font name is illegal
                if font_dict['font-name'].replace('Bold', '').replace('Italic', '').strip() not in list(tkfont.families()):
                    raise ValueError(f'{font_name} is not a valid font family; in {self.conf_path}')
            
            # otherwise raise an exception
            else:
                raise TypeError(f'"font-name" must be a string; in {self.conf_path}')

        # otherwise raise an exception
        else:
            raise KeyError(f'"font-name" not found; in {self.conf_path}')

        # check if font-size is present
        if 'font-size' in font_dict.keys():

            # get the font size
            font_size = font_dict['font-size']

            # check if font-size is an integer number
            if type(font_size) == int:

                # raise an exception if font size is not greater than zero
                if font_size < 1:
                    raise ValueError(f'"font-size" must be greater than 0; in {self.conf_path}')

            # otherwise raise an exception
            else:
                raise TypeError(f'"font-size" must be an integer; in {self.conf_path}')

        # otherwise raise an exception
        else:
            raise KeyError(f'"font-size" not found; in {self.conf_path}')

        # destroy the temporary tkinter window
        temp_tk.destroy()

        # return the tuple
        return (font_name, font_size)

    '''
    Method for loading the colour dictionary
    Expected value is a dictionary of all colours needed for the program to operate
    Returns a dictionary
    Raises an exception if dictionary is incomplete or contains corrupted values
    '''
    def _setColors(self):

        # read the key value
        colors = self.readKey('colors')

        # define required colours
        req_colors = ['background', 'success', 'info', 'warning', 'error', 'jegg']

        # regex for checking if a string is a hex color code
        reg_hex = "^#(?:[0-9a-fA-F]{3}){1,2}$"

        # check if dictionary containst all required folours
        for col in req_colors:

            # if colour code not present, raise an exception
            if col not in colors:
                raise KeyError(f'colour definition for "{col}" not found; in {self.conf_path}')

            # if colour value is not a hex color, raise an exception
            if not re.search(reg_hex, colors[col]):
                raise ValueError(f'colour value for "{col}" is not a valid hex colour code; in {self.conf_path}')

        # if all colours present and legal, return the dict
        return colors

    '''
    A function to prepare the overlay for operation
    Returns the root element
    '''
    def _setRoot(self, init_line):

        root = tk.Tk()
        root.title(init_line)

        # configure the overlay widget, aka the master widget of the line we have created
        root.overrideredirect(True)                                     # this prevents the override from behaving like a regular window
        root.geometry(f'+{self.position["X"]}+{self.position["Y"]}')    # this sets overlay's initial position
        root.minsize(500, 20)                                           # set minimum widget size to max of what it will ever be
        root.configure(bg=self.colors['background'])                    # set the BG colour of the widget
        root.wm_attributes('-topmost', True)                            # make sure the overlay widget stays on top of other windows
        root.wm_attributes('-alpha', self.opacity)                      # set opacity to make the widget semi-transparent

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