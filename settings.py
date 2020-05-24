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
        'loot': ['base_drops', 'behemoth', 'bonus_drops', 'deaths', 'detect', 'elite', 'time'],
        'trial': ['behemoth', 'result']
    }

    # expected target files
    TRG_FILES = {
        'bounty': ['draft', 'menu'],
        'loot': ['base_drops', 'detect', 'elite', 'token'],
        'trial': ['result']
    }

    '''
    Class initialiser, works mostly autonomously as everything it needs
    is stored in the appropriate configuration files or class variables
    '''
    def __init__(self):

        # determine the user name
        self.user = self._setUser()

        # detect installed Dauntless version
        self.game_ver = self._setGameVer()

        # load the list of possible cells
        self.cell_list = self._setCellList()

        # load the list of possible orbs
        self.orb_list = self._setOrbList()

        # load dictionary of ocr confusion
        self.confusion_dict = self._setConfusionDict()

        # load the dictionary of behemoth drops
        self.drop_dict = self._setDropDict()

        # load screen slices
        self.slice_dict = self._setSlices()

        # load target images
        self.target_dict = self._setTargets()





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