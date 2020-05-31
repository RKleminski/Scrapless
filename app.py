import pytesseract
import pyautogui
import os
import logging
import cv2
import random

import numpy as np

from uuid import uuid4
from datetime import datetime

from configurable import Configurable
from overlay import Overlay
from lobby_reader import LobbyReader
from loot_reader import LootReader

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
    PRG_VERS = '1.0.0'

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

        # initialise a loot reader
        self.loot_reader = LootReader()

        # data holders
        self.hunt_data = {}
        self.loot_data = {}
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

        # process the lobby if needed
        self._processLobby()

        # process the loot if needed
        self._processLoot()


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

        # in case of error, save current screen
        if colour == 'error':
            cv2.imwrite(f'debug_data/{uuid4()}.png', cv2.cvtColor(self.screen_capture, cv2.COLOR_RGB2BGR))

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
    Internal method for detecting and processing lobby screen. Convenience function to make other code
    more functional
    In: none
    Out: none
    '''
    def _processLobby(self):

        # try to read lobby only if no hunt data yet
        if len(self.hunt_data) == 0:

            # detect if the screen is a lobby
            if self.lobby_reader.detectScreen(self.screen_capture):

                # inform about detection
                self.writeOutput(f'Lobby screen detected, processing...', 'info')

                # process lobby screen and return data
                data = self.lobby_reader.readScreen(self.screen_capture)

                # determine if screen is valid
                if data['valid']:

                    # check if there is a behemoth name
                    if data['behemoth'] != '':

                        # report read data
                        self.writeOutput(f'Valid hunt detected: T{data["threat"]} ' + 
                                        f'{data["behemoth"]}, {data["tier"]} {data["type"]}. ' +
                                        f'Awaiting loot screen...', 'success')

                    # otherwise, if escalation screen
                    elif data['escalation'] != '':

                        # report on this
                        self.writeOutput(f'Valid hunt detected: {data["escalation"]}. ' +
                                        f'Loot data won\'t be recorded.', 'info')
                
                    # regardless, update the data
                    self.hunt_data = data

                # if not, report that to the user
                else:

                    # write out warning line
                    self.writeOutput(f'Invalid hunt detected, retrying...', 'warning')

    '''
    Internal method for detecting and processing lobby screen, Convenience function to make other code
    more functional
    '''
    def _processLoot(self):

        # try to read loot only if hunt data present
        if len(self.hunt_data) > 0 and len(self.loot_data) <= 0:

            # detect if screen is a loot screen
            if self.loot_reader.detectScreen(self.screen_capture):

                # process basic loot screen data
                data = self.loot_reader.readScreen(self.screen_capture)

                # check if the party was defeated
                if data['defeat']:

                    # inform the user, abandon processing
                    self.writeOutput(f'Party defeated, no data will be submitted', 'warning')

                # check for data validity
                elif data['behemoth'] == self.hunt_data['behemoth'] or self.hunt_data['behemoth'] in self.lobby_reader.valid_hunts.keys():

                    # inform that more in-depth reading will now take place
                    self.writeOutput(f'Valid loot screen detected, verifying...', 'info')

                    # update hunt data
                    self.hunt_data.update(data)

                    # attempt to read the loot
                    try:
                        # store loot data in memory
                        self.loot_data = self.loot_reader.readLoot(self.screen_capture, self.hunt_data['behemoth'])
                        self.loot_data = self._processLootData()

                        print(self.loot_data)

                    # in case OCR read anomalous stack of items, handle error internally
                    except ValueError as e:
                        self.writeOutput(e, 'error')

                # inform the reading will be attempted again
                else:
                    self.writeOutput(f'Invalid loot screen detected, retrying...', 'error')

    '''
    Internal method for sampling the loot data into what will be submitted
    In: nothing
    Out: sampled data
    '''
    def _processLootData(self):

        # determine slay roll count
        slay_rolls = 2 + (3 - self.hunt_data['deaths']) + (2 * self.hunt_data['elite'])

        # compensate for a bug with Elite loot display
        slay_rolls -= 2 * (self.hunt_data['tier'] == 'Heroic+' and 
                            self.hunt_data['behemoth'] not in ['Shrowd', 'Rezakiri'] and
                            self.hunt_data['elite'])

        # calculate how many drops to sample out from the data
        # sampling is necessary because of numerous display bugs on loot screen
        sample_count = slay_rolls * 2 if len(self.loot_data) >= slay_rolls * 2 else slay_rolls

        # fill submission data with dyes if present -- we always add dyes to submission data
        # because they can't drop from part break
        submit_data = [drop for drop in self.loot_data if drop['rarity'] == 'Artifact (Dye)']

        # data from which to draw samples
        source_data = [drop for drop in self.loot_data if drop['rarity'] != 'Artifact (Dye)']

        # draw the samples, reducing their number by dye drops present
        sample_data = random.sample(source_data, sample_count - len(submit_data))

        # return sampled data
        return [*submit_data, *sample_data]

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
