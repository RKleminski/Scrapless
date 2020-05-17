import json
import random
import string
import logging
import cv2
import sys
import os

from datetime import datetime
from uuid import uuid4
from glob import glob

from slice import Slice
from overlay import Overlay


'''
The class for storing configuration parametres
which will be used to operate the entirety of the 
application once running
'''
class AppSettings:

    #
    # class variables go here
    #
    # paths to config file
    CONF_PATH = './data/json/config.json'

    # logging paths
    LOG_PATH = './logging/log/'
    ERR_PATH = './logging/err/'

    # game paths
    MNF_PATH = 'C:/ProgramData/Epic/EpicGamesLauncher/Data/Manifests/'
    
    # drop-related paths
    CELL_PATH = './data/json/drops/cells.json'
    ORBS_PATH = './data/json/drops/orbs.json'
    DROP_PTH = './data/json/drops/behemoth.json'

    # OCR paths
    CNFS_PATH = './data/json/ocr/confusion.json'

    # screen path
    SCR_PATH = './data/json/screen'

    # targets path
    TRG_PATH = './data/targets'

    # expected slice files
    SLC_FILES = {
        'bounty': ['draft', 'menu', 'value'],
        'escalation': ['name', 'rank13', 'rank50', 'summary'],
        'lobby': ['behemoth', 'detect', 'hunt_type', 'threat'],
        'loot': ['base_drops', 'behemoth', 'bonus_drops', 'deaths', 'detect', 'elite', 'time'],
        'trial': ['behemoth', 'result']
    }

    # expected target files
    TRG_FILES = {
        'bounty': ['draft', 'menu'],
        'escalation': ['summary'],
        'lobby': ['detect', 'hunt_type'],
        'loot': ['base_drops', 'detect', 'elite', 'token'],
        'trial': ['result']
    }

    # huntdata paths
    HUNT_PATH = './data/json/huntdata/hunts.json'

    # data about this program 
    PRG_NAME = 'Scrapless'
    PRG_VERS = '0.9.8.6'

    # auxiliary data unlikely to change often enough to warrant putting it in configs
    # TODO: actually put these into files, to make things even more robust
    ELE_LIST = ['Blaze', 'Frost', 'Shock', 'Terra', 'Neutral', 'Umbral', 'Radiant']
    ESC_TIER = ['Escalation 1-13', 'Escalation 10-50']

    # list of colours expected in overlay config
    OVR_CLRS = ['background', 'success', 'info', 'warning', 'error', 'jegg']

    '''
    Class initialiser, works mostly autonomously as everything it needs
    is stored in the appropriate configuration files or class variables
    '''
    def __init__(self):

        # call the directory creation
        self.makeDirs()

        # instantiate the logger
        self.logger = self._setLogger()

        # load configuration file
        self.config = self._setConfig()

        # determine the user name
        self.user = self._setUser()

        # detect installed Dauntless version
        self.game_ver = self._setGameVer()

        # compute valid escalation names
        self.escalation_names = self._setEscalNames()

        # load a dictionary of valid hunts
        self.valid_hunts = self._setValidHunts()

        # load the list of possible cells
        self.cell_list = self._setCellList()

        # load the list of possible orbs
        self.orb_list = self._setOrbList()

        # load dictionary of ocr confusion
        self.confusion_dict = self._setConfusionDict()

        # load the dictionary of behemoth drops
        self.drop_dict = self._setDropDict()

        # load TesseractOCR path
        self.tesseract_path = self._setTesseractPath()

        # load screen slices
        self.slice_dict = self._setSlices()

        # load target images
        self.target_dict = self._setTargets()

    '''
    Create folders required for the program operations as necessary
    '''
    def makeDirs(self):

        # iterate over necessary paths
        for path in [self.LOG_PATH, self.ERR_PATH]:

            # create folder if it does not exist
            if not os.path.exists(path):
                os.makedirs(path)

    '''
    Function for retrieving the logger, configured to separately handle
    info and error messages
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
    Load the config.json file into memory in a dict version
    Raise an exception if the file cannot be found
    '''
    def _setConfig(self):

        # check if file exists
        if os.path.exists(self.CONF_PATH):

            # open config file
            with open(self.CONF_PATH, 'r') as conf_file:
                config = json.load(conf_file)

            # inform user of a successful access to the file
            self.logger.info('SETUP: config.json file read successfully')

            # return the config file
            return config

        # raise exception if we can't access the file
        raise FileNotFoundError(f'file {self.CONF_PATH} could not be found')

    '''
    Function to initalise random user ID if the person running the program
    decides to remain anonymous
    '''
    def _setUser(self):

        # check if user field exists
        if ('user' in self.config.keys()):

            # check if user field has a name field
            if ('name' in self.config['user'].keys()):

                # fetch the declared name
                user_name = self.config['user']['name']

                # check if the name is filled
                if user_name != '':

                    # announce success
                    self.logger.info(f'SETUP: username set to {user_name}')

                    # return the selected name
                    return user_name

                # otherwise generate a random ID
                else:
                    
                    # announce the random generation to the user
                    self.logger.info('SETUP: no username found, generating a random user ID and saving to disk')

                    # generate the ID
                    user_name = uuid4()

                    # overwrite config on disk
                    self.config['user']['name'] = user_name

                    # save updated config
                    with open(self.CONF_PATH, 'w') as dump_file:
                        json.dump(self.config, dump_file, indent=2, separators=(',',':'))

                    # return the generated name
                    return user_name
            
            else:
                raise KeyError(f'Key "name" not found in "user" in {self.CONF_PATH}')
        
        else:
            raise KeyError(f'Key "user" not found in {self.CONF_PATH}')

    '''
    Automatically accesses the manifest file created by Epic Games Store
    and retrieves the current game version (patch)
    '''
    def _setGameVer(self):

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

                        # announce success
                        self.logger.info(f'SETUP: detected Dauntless version {patch_ver}')

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
    Set possible Escalation names in an array form
    This can be used to verify validity of read Escalations
    '''
    def _setEscalNames(self):

        # combine tiers of escalations with elements
        esca_names = [f'{elem} {tier}' for elem in self.ELE_LIST for tier in self.ESC_TIER]

        # return the list
        return esca_names

    '''
    Read the file listings for valid hunts that can be encountered in the game
    And return its content so it can be set in appropriate variable
    '''
    def _setValidHunts(self):

        # check if hunt config file exists
        if os.path.exists(self.HUNT_PATH):

            # open the file and parse JSON contents
            with open(self.HUNT_PATH, 'r') as load_file:
                valid_hunts = json.load(load_file)

            # inform about success
            self.logger.info(f'SETUP: successfully loaded valid hunts')

            # return the dict read from JSON
            return valid_hunts

        # raise an exception otherwise
        raise FileNotFoundError(f'file {self.HUNT_PATH} could not be found')

    '''
    Read the universal drop file and load cell list from there
    '''
    def _setCellList(self):

        # check if the file exists
        if os.path.exists(self.CELL_PATH):

            # open the file 
            with open(self.CELL_PATH, 'r') as load_file:

                # parse the JSON contents and extarct the relevant part
                json_file = json.load(load_file)

                # check if file has Cells info
                if 'Cells' in json_file.keys():

                    # log the success
                    self.logger.info(f'SETUP: successfully loaded Cell list')

                    # return the list
                    return json_file['Cells']

                # raise an exception otherwise
                raise KeyError(f'The key "Cells" not found in {self.UDRP_PATH} file')

        # raise an exception otherwise
        raise FileNotFoundError(f'file {self.UDRP_PATH} could not be found')

    '''
    Read the universal drop file and load orb list from there
    '''
    def _setOrbList(self):

        # check if the file exists
        if os.path.exists(self.ORBS_PATH):

            # open the file 
            with open(self.ORBS_PATH, 'r') as load_file:

                # parse the JSON contents and extarct the relevant part
                json_file = json.load(load_file)

                # check if file has Orbs info
                if 'Orbs' in json_file.keys():

                    # log the success
                    self.logger.info(f'SETUP: successfully loaded Orbs list')

                    # return the list
                    return json_file['Orbs']

                # raise an exception otherwise
                raise KeyError(f'The key "Orbs" not found in {self.UDRP_PATH} file')

        # raise an exception otherwise
        raise FileNotFoundError(f'file {self.UDRP_PATH} could not be found')

    '''
    Read the file containing typical confusion of characters or 
    strings of characters when TesseractOCR reads drop counts 
    in the loot screen
    '''
    def _setConfusionDict(self):

        # check if the file exists
        if os.path.exists(self.CNFS_PATH):

            # read file from path
            with open(self.CNFS_PATH, 'r') as load_file:

                # translate to JSON
                confusion_dict = json.load(load_file)

                # inform about successful reading
                self.logger.info(f'SETUP: successfully loaded OCR character confusion dictionary')

                # return the dictionary
                return confusion_dict

        # raise an exception otherwise
        raise FileNotFoundError(f'file {self.CNFS_PATH} could not be found')

    '''
    Read the file containing the names and rarities of drops 
    for each behemoth, then set it into a variable
    '''
    def _setDropDict(self):

        # check if the file exists
        if os.path.exists(self.DROP_PTH):

            # read the file from path
            with open(self.DROP_PTH, 'r') as load_file:

                # parse as a JSON
                drop_dict = json.load(load_file)

                # communicate success
                self.logger.info(f'SETUP: successfully loaded behemoth drops')

                # return the dictionary
                return drop_dict

        # otherwise raise an exception
        raise FileNotFoundError(f'file {self.DROP_PTH} could not be found')

    '''
    Retrieve Tesseract path from configuration file
    '''
    def _setTesseractPath(self):

        # check if the key exists in configuration
        if 'paths' in self.config.keys():

            # retrieve paths dict
            paths = self.config['paths']

            # check if tesseract path is in there
            if 'tesseract' in paths:

                # retrieve the path
                tess_path = paths['tesseract']

                # check if the path is correct
                if os.path.exists(tess_path):

                    # inform about success
                    self.logger.info(f'SETUP: successfully loaded Tesseract OCR location')

                    # return the location
                    return tess_path

                # otherwise raise an exception
                raise FileNotFoundError(f'file {tess_path} could not be found')

            # otherwise raise exception
            raise KeyError(f'key "tesseract" not found in configuration file')

        # otherwise raise exception
        raise KeyError(f'key "paths" not found in configuration file')

    '''
    Set a dictionary of slices for accurately detecting,
    reading and processing any given screen
    '''
    def _setSlices(self):

        # prepare empty dictionary
        slices = {}

        # fill it with dictionaries for specific screens
        for key in self.SLC_FILES.keys():
            
            # construct the folder path
            path =  f'{self.SCR_PATH}/{key}'

            # check if the path exists
            if os.path.isdir(path):

                # create an empty dict for a screen
                slices[key] = {}

                # iterate over slice names for the screen
                for name in self.SLC_FILES[key]:

                    # construct the path to slice file
                    path = f'{self.SCR_PATH}/{key}/{name}.json'

                    # add slice to the dictionary
                    slices[key][name] = Slice(json_path=path)

            # otherwise raise an exception
            else:
                raise NotADirectoryError(f'{path} is not a directory')

        # communicate success
        self.logger.info(f'SETUP: succesfully loaded screen region configuration')

        # return the dictionary
        return slices

    '''
    Set a dictionary of target images for the recognition
    and detection of specific screens
    '''
    def _setTargets(self):

        # prepare empty dictionary
        targets = {}

        # fill it with dictionaries for specific screens
        for key in self.TRG_FILES.keys():
            
            # construct the folder path
            path =  f'{self.TRG_PATH}/{key}'

            # check if the path exists
            if os.path.isdir(path):

                # create an empty dict for a screen
                targets[key] = {}

                # iterate over target names for the screen
                for name in self.TRG_FILES[key]:

                    # construct the path to target file
                    path = f'{self.TRG_PATH}/{key}/{name}.png'

                    # check if the file exists
                    if os.path.isfile(path):

                        # add target to the dictionary
                        targets[key][name] = cv2.imread(path, 0)

                    # otherwise raise an exception
                    else:
                        raise FileNotFoundError(f'file {path} could not be found')

            # otherwise raise an exception
            else:
                raise NotADirectoryError(f'{path} is not a directory')

        # communicate success
        self.logger.info(f'SETUP: succesfully loaded target images')

        # return the dictionary
        return targets

    '''
    Read the config file and instantiate an overlay from there
    Important to note is that this method is intended to be used 
    to receive the overlay outside of the setting class, for easier
    use with the rest of the app
    '''
    def configureOverlay(self):

        # check if overlay configuration found in config.json
        if 'overlay' in self.config.keys():

            # retrieve overlay config
            overlay_config = self.config['overlay']

            # check if overlay toggle is defined
            if 'enable' in overlay_config.keys():

                # read the value and convert to lowercase
                enable = overlay_config['enable'].lower()

                # check field's value to determine if it is legal
                if enable in ['yes', 'no']:

                    # if not enabled, exit early and return null
                    if enable == 'no':
                        return None

                # otherwise raise an exception
                else:
                    raise ValueError(f'key "enable" can only have a value of "Yes" or "No" (case insensitive) in {self.CONF_PATH}')
            # otherwise raise an exception
            else:
                raise KeyError(f'key "enable" could not be found in {self.CONF_PATH}')

            # check if opacity is defined
            if 'opacity' in overlay_config.keys():

                # retrieve value
                opacity = overlay_config['opacity'] / 100.0
            # otherwise raise an exception
            else:
                raise KeyError(f'key "opacity" could not be found in {self.CONF_PATH}')

            # check for overlay position config
            if 'position' in overlay_config.keys():

                # retrieve the position dict
                pos_config = overlay_config['position']

                # check for coordinate X key
                if 'X' in pos_config.keys():

                    # check if the coordinate is a valid number
                    if pos_config['X'] != '':

                        # retrieve value
                        pos_x = pos_config['X']

                    # otherwise raise an exception
                    else: 
                        raise ValueError(f'key "X" has no defined value in {self.CONF_PATH}')

                # otherwise raise an exception
                else:
                    raise KeyError(f'key "X" could not be found in {self.CONF_PATH}')


                # check for coordinate Y key
                if 'Y' in pos_config.keys():

                    # check if the coordinate is a valid number
                    if pos_config['Y'] != '':

                        # retrieve value
                        pos_y = pos_config['Y']

                    # otherwise raise an exception
                    else: 
                        raise ValueError(f'key "Y" has no defined value in {self.CONF_PATH}')

                # otherwise raise an exception
                else:
                    raise KeyError(f'key "Y" could not be found in {self.CONF_PATH}')
            # otherwise raise an exception
            else:
                raise KeyError(f'key "position" could not be found in {self.CONF_PATH}')

            # check if output section is defined
            if 'output' in overlay_config.keys():

                # read output config
                output_config = overlay_config['output']

                # check if max_lines are defined
                if 'max_lines' in output_config.keys():

                    # check if the value is not empty
                    if output_config['max_lines'] != '':

                        # retrieve the value
                        max_lines = output_config['max_lines']

                    # otherwise raise an exception
                    else:
                        raise ValueError(f'key "max_lines" has no defined value in {self.CONF_PATH}')
                # otherwise raise an exception
                else:
                    raise KeyError(f'key "max_lines" could not be found in {self.CONF_PATH}')


                # check if font is defined
                if 'font' in output_config.keys():

                    # check if the value is not empty
                    if output_config['font'] != '':

                        # retrieve the value
                        font = output_config['font']

                    # otherwise raise an exception
                    else:
                        raise ValueError(f'key "font" has no defined value in {self.CONF_PATH}')
                # otherwise raise an exception
                else:
                    raise KeyError(f'key "font" could not be found in {self.CONF_PATH}')


                # check if font-size is defined
                if 'font-size' in output_config.keys():

                    # check if the value is not empty
                    if output_config['font-size'] != '':

                        # retrieve the value
                        font_size = output_config['font-size']

                    # otherwise raise an exception
                    else:
                        raise ValueError(f'key "font-size" has no defined value in {self.CONF_PATH}')
                # otherwise raise an exception
                else:
                    raise KeyError(f'key "font-size" could not be found in {self.CONF_PATH}')
            # otherwise raise an exception
            else:
                raise KeyError(f'key "output" could not be found in {self.CONF_PATH}')

            # check if colors section is defined
            if 'colors' in overlay_config.keys():

                # get the colour dictionary
                color_dict = overlay_config['colors']

                # check if the dictionary contains all of the expected colours
                for col in self.OVR_CLRS:
                    if col not in color_dict.keys():
                        raise KeyError(f'key {col} could not be found in {self.CONF_PATH}')
            # otherwise raise an exception
            else:
                raise KeyError(f'key "colors" could not be found in {self.CONF_PATH}')

            #
            # if all parametres read properly communicate success
            #
            self.logger.info(f'SETUP: successfully loaded screen overlay')
            #
            # and instantiate new overlay
            #
            return Overlay(f'SCRAPLESS {self.PRG_VERS}', opacity, pos_x, pos_y, 
                        max_lines, font, font_size, color_dict)

        # otherwise raise an exception
        raise KeyError(f'key "overlay" could not be found in {self.CONF_PATH}')