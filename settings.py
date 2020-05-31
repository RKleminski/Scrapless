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

    # expected slice files
    SLC_FILES = {
        'bounty': ['draft', 'menu', 'value'],
    }

    # expected target files
    TRG_FILES = {
        'bounty': ['draft', 'menu'],
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

        # load dictionary of ocr confusion
        self.confusion_dict = self._setConfusionDict()

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