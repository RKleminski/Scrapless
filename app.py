import pytesseract
import pyautogui
import os
import logging

import numpy as np

from datetime import datetime

from configurable import Configurable
from overlay import Overlay
from lobby_reader import LobbyReader

'''
Primary application class, with all necessary components
stored as instance variables, initialised on startup
This is the heart of the application
'''
class App(Configurable):

    #
    #   CLASS VARIABLES
    #
    # data about this program 
    PRG_NAME = 'Scrapless'
    PRG_VERS = '1.0.0.0'

    # path for config file
    SLF_PATH = './data/json/config/config.json'

    # path to manifest folder
    MNF_PATH = 'C:/ProgramData/Epic/EpicGamesLauncher/Data/Manifests/'

    # logging paths
    LOG_PATH = './logging/log/'
    ERR_PATH = './logging/err/'

    def __init__(self):
        
        # call parent class constructor
        Configurable.__init__(self, self.SLF_PATH)

        # create logging folders
        self._makeLogDirs()

        # initialise the logger
        self.logger = self._setLogger()

        # initialise overlay
        self.overlay = Overlay(f'{self.PRG_NAME.upper()} {self.PRG_VERS}')

        # initialise screen capture as empty
        self.screen_capture = None

        # point pytesseract at tesseract installation
        self._setPyTesseract()

        # initialise a lobby reader
        self.lobby_reader = LobbyReader()

        # data holders
        self.hunt_data = {}
        self.bounty_data = {}

    '''
    Capture new screenshot and store it within
    the instance of this class
    '''
    def screenCap(self):

        # take the screencap
        screencap = pyautogui.screenshot(region=(0, 0, 1920, 1080))

        #  overwrite the capture with screencap converted to a numpy array
        self.screen_capture = np.array(screencap)

    '''
    Main method of operation, calls associated readers to detect the screen and read it out
    if recognised.
    '''
    def processScreen(self):

        # try to read lobby only if no hunt data yet
        if len(self.hunt_data) == 0:

            # detect if the screen is a lobby
            if self.lobby_reader.detectScreen(self.screen_capture):

                # inform about detection
                self.writeOutput(f'Lobby screen detected, processing...', 'info')

                # process lobby screen and return data
                self.hunt_data = self.lobby_reader.readScreen(self.screen_capture)

                # determine if screen is valid
                if self.hunt_data['valid']:

                    # check if there is a behemoth name
                    if self.hunt_data['behemoth'] != '':

                        # report read data
                        self.writeOutput(f'Valid hunt detected: T{self.hunt_data["threat"]} ' + 
                                        f'{self.hunt_data["behemoth"]}, {self.hunt_data["type"]}. ' +
                                        f'Awaiting loot screen...', 'success')

                    # otherwise, if escalation screen
                    elif self.hunt_data['escalation'] != '':

                        # report on this
                        self.writeOutput(f'Valid hunt detected: {self.hunt_data["escalation"]}. ' +
                                        f'Loot data won\' be recorded.', 'info')
                
                # if not, report that to the user
                else:

                    # write out warning line
                    self.writeOutput(f'Invalid hunt detected, retrying...', 'warning')

    '''
    Method for printing out an output to logs and to overlay
    This is a convenience function to reduce clutter and keep 
    user information level high
    '''
    def writeOutput(self, text, colour):

        # only call the overlay method if said overlay is enabled
        if self.overlay:
            self.overlay.writeLine(text.replace('\n', ''), colour)

        # write out to log
        self.logger.info(text)

    '''
    Method for creating folders for logging
    In: nothing
    Out: nothing
    '''
    def _makeLogDirs(self):

        # iterate over necessary paths
        for path in [self.LOG_PATH, self.ERR_PATH]:

            # create folder if it does not exist
            if not os.path.exists(path):
                os.makedirs(path)

    '''
    Method for initialising the logger and returning it
    In: nothing
    Out: logger object
    '''
    def _setLogger(self):

        # compose file name containing date and name of the program
        file_name = f'{datetime.now().date()}_{self.PRG_NAME.lower()}'

        # set some basic information to work from going forward
        LOG_FRMT = '%(asctime)s %(message)s'
        DATE_FMT = '%d/%m/%Y %H:%M:%S'
        LOG_NAME = 'scrapless'
        INF_FILE = f'{self.LOG_PATH}{file_name}.log'
        ERR_FILE = f'{self.ERR_PATH}{file_name}.err'
        
        # create logger and configure its format
        logger = logging.getLogger(LOG_NAME)
        log_formatter = logging.Formatter(LOG_FRMT)

        # create a stream handler so logging goes to console
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(log_formatter)
        logger.addHandler(stream_handler)

        # configure the logger for INFO logging
        # appending to files to support multiple sessions in one day
        file_handler_info = logging.FileHandler(INF_FILE, mode='a')
        file_handler_info.setFormatter(log_formatter)
        file_handler_info.setLevel(logging.INFO)
        logger.addHandler(file_handler_info)

        # configure the logger for ERROR logging
        # appending to files to support multiple sessions in one day
        file_handler_error = logging.FileHandler(ERR_FILE, mode='a')
        file_handler_error.setFormatter(log_formatter)
        file_handler_error.setLevel(logging.ERROR)
        logger.addHandler(file_handler_error)

        # set logger level to INFO and higher
        logger.setLevel(logging.INFO)

        return logger

    '''
    Method for configuring PyTesseract from config file
    Reads the path and sets it to a global value
    Raises an exception if the path is missing or does not point to a file
    '''
    def _setPyTesseract(self):

        # retrieve tesseract path from config
        tess_path = self.readKey('tesseract')

        # verify the path is a string
        if type(tess_path) == str:

            # verify path leads to a file
            if os.path.isfile(tess_path):

                # use the path read from config to setup pytesseract
                pytesseract.pytesseract.tesseract_cmd = tess_path
            
                # return the path
                return tess_path

            # otherwise raise an exception
            raise FileNotFoundError(f'file {tess_path} is not a file or could not be read')
