import pytesseract
import pyautogui
import os
import logging
import cv2
import random
import json
import time

import numpy as np

from glob import glob
from uuid import uuid4
from datetime import datetime
from requests import HTTPError

from configurable import Configurable
from overlay import Overlay
from lobby_reader import LobbyReader
from loot_reader import LootReader
from bounty_reader import BountyReader
from data_sender import DataSender

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
    PRG_VERS = '1.0.1.3'

    # path for config file
    SLF_PATH = './data/json/config/config.json'

    # path to manifest folder
    MNF_PATH = 'C:/ProgramData/Epic/EpicGamesLauncher/Data/Manifests/'

    # logging paths
    LOG_PATH = './logging/log/'
    ERR_PATH = './logging/err/'
    IMG_PATH = './logging/img/'

    # max exceptions before abandoning the reading
    MAX_EXC = 5

    # time variables
    LOOP_INTER = 0.2
    BNTY_INTER = 1.5
    LBBY_INTER = 0.25
    LOOT_INTER = 0.5

    def __init__(self):
        
        # PREPARE LOGGING FIRST TO ENSURE
        # THE ABILITY TO OUTPUT ERROR LOGS
        #
        # create logging folders
        self._makeLogDirs()

        # initialise the logger
        self.logger = self._setLogger()

        # catch exceptions to log them
        try:

            # call parent class constructor
            Configurable.__init__(self, self.SLF_PATH)

            # initialise overlay
            self.overlay = Overlay(f'{self.PRG_NAME.upper()} {self.PRG_VERS}')
            
            # point pytesseract at tesseract installation
            self._setPyTesseract()

            # initialise a lobby reader
            self.lobby_reader = LobbyReader()

            # initialise a loot reader
            self.loot_reader = LootReader()

            # initialise a bounty reader
            self.bounty_reader = BountyReader()

            # initialise a data sender
            self.data_sender = DataSender()

            # read user from config file
            self.user = self._setUser()

            # read game patch
            self.patch = self._setGamePatch()

            # initialise screen capture as empty
            self.screen_capture = None

            # data holders
            self.bounty_data = {}
            self.lobby_data = {}
            self.loot_data = []

            # exception counter for repeated issue handling
            self.exc_counter = 0

            # welcome the user
            self.welcomeMessage()

        except Exception as e:

            # log the exception
            self.logger.error(str(e))

            # shut down the app
            quit()

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

        # process bounty draft if needed
        self._processBounty()

        # submit data if needed
        self._submitData()

    '''
    Method for quickly clearing all data in the app
    '''
    def clearData(self):

        # return data holders to base state
        self.bounty_data = {}
        self.lobby_data = {}
        self.loot_data = []

    '''
    Method for writing out a welcome message in the application
    '''
    def welcomeMessage(self):

        self.logger.info(f'==== WELCOME TO SCRAPLESS {self.PRG_VERS} ====')
        self.logger.info(f'Dauntless ver {self.patch}')
        self.logger.info(f'Username set to {self.user}')

        print('\n')

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

        # in case of a success
        if colour == 'success':

            # reset exception counter
            self.exc_counter = 0

        # in case of error
        if colour == 'error':

            # save current screen
            cv2.imwrite(f'{self.IMG_PATH}{uuid4()}.png', cv2.cvtColor(self.screen_capture, cv2.COLOR_RGB2BGR))

            # clear data
            self.clearData()

    '''
    Internal method for keeping track of repeating reading issues; clears all data
    after enough issues happened
    '''
    def _incrementException(self):

        # increment exception counter
        self.exc_counter += 1

        # check if exception count exceeded max
        if self.exc_counter >= self.MAX_EXC:

            # write out an error message
            self.writeOutput(f'Repeated issues detected. Screenshot saved, all data flushed', 'error')

            # reset exception counter
            self.exc_counter = 0

    '''
    Method for creating folders for logging
    In: nothing
    Out: nothing
    '''
    def _makeLogDirs(self):

        # iterate over necessary paths
        for path in [self.LOG_PATH, self.ERR_PATH, self.IMG_PATH]:

            # create folder if it does not exist
            if not os.path.exists(path):
                os.makedirs(path)

    '''
    Internal method for detecting and processing bounty draft
    Updates bounty data as a result, unless an exception happens
    '''
    def _processBounty(self):

        # read only if both bounty and loot data is empty
        if len(self.bounty_data) <= 0 and len(self.loot_data) <= 0:
            
            # proceed if draft can be detected
            if self.bounty_reader.detectDraftStart(self.screen_capture):

                # inform the user about the fact
                self.writeOutput(f'Bounty draft detected, processing...', 'info')

                # wait out the initial animation
                time.sleep(self.BNTY_INTER)

                # enter a loop of attempting to read the bounty
                self._processBountyLoop()

    '''
    Convenience function to keep attempting a bounty read until succeeding or
    detecting that user exited the screen
    '''
    def _processBountyLoop(self):

        # keep looping until valid bounty was read, or the user left the draft screen
        while len(self.bounty_data) <= 0 and not self.bounty_reader.detectDraftEnd(self.screen_capture):

            # capture a new screenshot
            self.screenCap()

            # attempt to read the bounty
            try:

                # store the data 
                self.bounty_data = self.bounty_reader.readScreen(self.screen_capture)

                # inform the user
                self.writeOutput(f'{self.bounty_data["rarity"]} bounty detected. Awaiting draft end...', 'success')

            # in case illegal value was found
            except ValueError as e:
                self.writeOutput(str(e), 'warning')

            # wait briefly to get a better screen read
            time.sleep(self.LOOP_INTER)

    '''
    Internal method for detecting and processing lobby screen
    more functional
    Updates lobby data as a result, unless an exception happens
    '''
    def _processLobby(self):

        # try to read lobby only if no hunt data yet
        if len(self.lobby_data) <= 0:

            # detect if the screen is a lobby
            if self.lobby_reader.detectScreen(self.screen_capture):

                # inform about detection
                self.writeOutput(f'Lobby screen detected, processing...', 'info')

                # wait briefly to avoid unnecessary errors
                time.sleep(self.LBBY_INTER)

                # enter the lobby-reading loop
                self._processLobbyLoop()

    '''
    Convenience function to keep attempting a lobby read until succeeding or
    detecting that user exited the screen
    '''
    def _processLobbyLoop(self):

        # while we can still see the lobby and we have no lobby data
        while self.lobby_reader.detectScreen(self.screen_capture) and len(self.lobby_data) <= 0:

            # update screen grab
            self.screenCap()

            # attempt reading the screen
            try:

                # process lobby screen and save the data
                self.lobby_data = self.lobby_reader.readScreen(self.screen_capture)

                # write appropriate output
                self._processLobbyOutput()

            # handle an exception
            except ValueError as e:

                # communicate the exception to the user
                self.writeOutput(str(e), 'warning')

            # wait briefly to get a better screen read
            time.sleep(self.LOOP_INTER)

    '''
    Convenience function encompassing all possible text output for
    when the program has read the lobby without any issues
    '''
    def _processLobbyOutput(self):

        # get data to memory briefly, to simplify access
        data = self.lobby_data

        # if trial screen
        if 'Trial' in data['tier']:

            # report on trial tier
            self.writeOutput(f'{data["tier"]} detected', 'success')

        # otherwise, if escalation screen
        elif data['escalation'] != '':

            # report on escalation
            self.writeOutput(f'Valid hunt detected: {data["escalation"]}. ' +
                            f'Loot data won\'t be recorded.', 'info')                    

        # otherwise, if actual behemoth
        elif data['behemoth'] != '':

            # report read data
            self.writeOutput(f'Valid hunt detected -- T{data["threat"]} ' + 
                            f'{data["behemoth"] if data["behemoth"] != data["tier"] else ""}' +
                            f'{", " if data["behemoth"] != data["tier"] else ""}' +
                            f'{data["tier"]} {data["type"]}. ' +
                            f'Awaiting loot screen...', 'success')

    '''
    Internal method for detecting and processing loot screen
    Updates loot data as a result, unless an exception happens
    In: none
    Out: none
    '''
    def _processLoot(self):

        # try to read loot only if lobby data present
        if len(self.lobby_data) > 0 and len(self.loot_data) <= 0:

            # if trial, detect for trial end screen
            if 'Trial' in self.lobby_data['tier']:
                
                # check for trial end screen
                if self.loot_reader.detectTrialEnd(self.screen_capture):

                    # inform the user, abandon processing
                    self.writeOutput(f'{self.lobby_data["tier"]} has ended', 'success')
                    self.clearData()


            # otherwise detect for loot screen
            else:

                # detect if screen is a loot screen
                if self.loot_reader.detectLootScreen(self.screen_capture):

                    # check if the hunt was an Escalation
                    if self.lobby_data['escalation'] != '':

                        # inform the user, abandon processing
                        self.writeOutput(f'Escalation run ended, no data will be submitted', 'success')
                        self.clearData()

                    # otherwise enter the loop of reading the screen
                    else:

                        # wait briefly to ensure animation end
                        time.sleep(self.LOOT_INTER)

                        # start the loop
                        self._processLootLoop()

    '''
    Convenience function for loot screen reading loop
    '''
    def _processLootLoop(self):

        # only try reading until we have loot data or until we leave the screen
        while len(self.loot_data) <= 0 and self.loot_reader.detectLootScreen(self.screen_capture) and len(self.lobby_data) > 0:

            # take a new screencap
            self.screenCap()

            # process basic loot screen data
            data = self.loot_reader.readScreen(self.screen_capture)

            # check if the party was defeated
            if data['defeat']:

                # inform the user, abandon processing
                self.writeOutput(f'Party defeated, no data will be submitted', 'warning')
                self.clearData()


            # otherwise, check if valid hunt
            elif data['behemoth'] == self.lobby_data['behemoth'] or self.lobby_data['behemoth'] in self.lobby_reader.valid_hunts.keys():

                # inform that more in-depth reading will now take place
                self.writeOutput(f'Loot screen detected, verifying...', 'info')

                # update lobby data
                self.lobby_data.update(data)

                # attempt to read the loot
                try:
                    # store loot data in memory
                    self.loot_data = self.loot_reader.readLoot(self.screen_capture, self.lobby_data['behemoth'])
                    self.loot_data = self._processLootData()

                    # inform that everything is okay
                    self.writeOutput(f'Valid loot data read, you may now leave the screen', 'success')

                # in case OCR read anomalous stack of items, handle error internally
                except ValueError as e:
                    self.writeOutput(str(e), 'error')

            # inform the reading will be attempted again
            else:
                self.writeOutput(f'Expected behemoth {self.lobby_data["behemoth"]} but found ' + 
                                f'{data["behemoth"]}, retrying...', 'warning')
                self._incrementException()

            # wait briefly to get a better screenshot
            time.sleep(self.LOOP_INTER)

    '''
    Internal method for sampling the loot data into what will be submitted
    In: nothing
    Out: sampled data
    '''
    def _processLootData(self):

        # determine slay roll count
        slay_rolls = 2 + (3 - self.lobby_data['deaths']) + (2 * self.lobby_data['elite'])

        # compensate for a bug with Elite loot display
        slay_rolls -= 2 * (self.lobby_data['tier'] == 'Heroic+' and 
                            self.lobby_data['behemoth'] not in ['Shrowd', 'Rezakiri'] and
                            self.lobby_data['elite'])

        # calculate how many drops to sample out from the data
        # sampling is necessary because of numerous display bugs on loot screen
        sample_count = slay_rolls * 2 if len(self.loot_data) >= slay_rolls * 2 else slay_rolls

        # fill submission data with dyes and cells if present -- we always add them to submission data
        # because they can't drop from part break
        submit_data = [drop for drop in self.loot_data if drop['rarity'] in ['Artifact (Dye)', 'Rare (Cell)', 'Uncommon (Cell)']]

        # data from which to draw samples
        source_data = [drop for drop in self.loot_data if drop['rarity'] not in ['Artifact (Dye)', 'Rare (Cell)', 'Uncommon (Cell)']]

        # in the event of sample count being higher than valid loot, take number of items
        # in the loot - this is a safeguard against low-level hunts dropping part breaks on
        # slay rolls
        sample_count = min(sample_count, len(self.loot_data))

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

    '''
    Internal method to automatically accesses the manifest file created by Epic Games Store
    In: none
    Out: string number of game version
    '''
    def _setGamePatch(self):

        # check if the manifest folder exists
        if os.path.isdir(self.MNF_PATH):

            # get the manifest items in the directory
            manifs = glob(self.MNF_PATH + '*.item')

            # check if there are any manifest items there
            if len(manifs) > 0:

                # iterate over file paths
                for item_path in manifs:

                    # open a manifest file
                    item_file = open(item_path, 'r')

                    # parse file into JSON
                    item = json.load(item_file)

                    # check if the file contains Dauntless data
                    if item['DisplayName'] == 'Dauntless':

                        # get patch version
                        patch_ver = '.'.join(item['AppVersionString'].split('.')[:3])

                        # return patch version
                        return patch_ver

                # raise an exception if we iterated through all items without finding 
                # a Dauntless manifest
                raise FileNotFoundError(f'Dauntless manifest file could not be found')

            # if not, raise an exception
            else:
                raise FileNotFoundError(f'no manifest files found in {self.MNF_PATH}')

        # if not, raise exception
        else:
            raise NotADirectoryError(f'{self.MNF_PATH} is not a directory')

    '''
    Internal method for initialising the user and checking all necessary details about them
    In: none
    Out: string name of user
    '''
    def _setUser(self):

        # read the user key from config file
        user = self.readKey('user')

        # check if the user value is empty
        if user == '':

            # replace empty name with random ID string
            user = str(uuid4())

            # create an updated version of the config to over-write current one with
            new_conf = self.conf_file

            # overwrite user value
            new_conf['user'] = user

            # overwrite the file
            with open(self.conf_path, 'w') as write_file:
                json.dump(self.conf_file, write_file, indent=2, separators=(',',':'))

        # return the user name
        return user

    '''
    Internal method for submitting data, based on what data is filled at the moment
    In: none
    Out: none
    '''
    def _submitData(self):

        # if loot data is not empty, submit loot data
        if len(self.loot_data) > 0:

            # iterate over drops
            for drop in self.loot_data:

                # add game and patch data
                drop['user'] = self.user
                drop['patch'] = self.patch
                drop['behemoth'] = self.lobby_data['behemoth']
                drop['threat'] = self.lobby_data['threat']
                drop['tier'] = self.lobby_data['tier']

                # try submitting the drop
                try:
                    # send POST request
                    self.data_sender.submitData(drop, 'loot')
        
                # raise exception if encountered
                except HTTPError as e:
                    self.writeOutput(str(e), 'error')

            # inform about data submission
            self.writeOutput(f'Loot data submitted', 'success')

            # clear the data
            self.clearData()

        # if bounty data is not empty
        if len(self.bounty_data) > 0:

            # check if draft screen was closed
            if self.bounty_reader.detectDraftEnd(self.screen_capture):

                # add game and patch data
                self.bounty_data['user'] = self.user
                self.bounty_data['patch'] = self.patch

                # try submitting the bounty
                try:
                    # send a POST request
                    self.data_sender.submitData(self.bounty_data, 'bounty')

                    # inform about data submission
                    self.writeOutput(f'Bounty data submitted', 'success')

                # raise exception if encountered
                except HTTPError as e:
                    self.writeOutput(str(e), 'error')

                # empty the data
                self.clearData()