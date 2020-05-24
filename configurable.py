import os
import json

'''
A generic class for inheritance by all the other classes in the project
Provides the framework for easily reading an associated config file
and a method for extracting any key from said file
===
This is meant to be used as a way to reduce code duplication
and standardise exception handling. Any class capable of being configured
should inherit after this class
'''
class Configurable:

    '''
    Initialise the class using passed path; save it in the instance variable
    then proceed to load the config file it relates to; initialising will raise
    an exception if the path is invalid
    '''
    def __init__(self, conf_path):

        # configuration path
        self.conf_path = conf_path

        # read config file from the path
        self.conf_file = self._setConfigFile()

    '''
    A generic method for reading a config file into class memory
    Raises an exception when the file can't be accessed
    '''
    def _setConfigFile(self):

        # call the readFile for config file
        conf_file = self.readFile(self.conf_path)

        # return read file
        return conf_file

    '''
    A generic method for reading a file from path. 
    Raises an exception when file can't be accessed.
    In: file path
    Out: read file
    '''
    def readFile(self, file_path):

        # check if the file exists
        if os.path.isfile(file_path):

            # load the file
            with open(file_path, 'r') as load_file:
                
                # parse as json file
                conf_file = json.load(load_file)

                # return the result
                return conf_file

        # otherwise raise an exception
        raise FileNotFoundError(f'file {file_path} is not a file or could not be read')


    '''
    A generic method for reading and returning a specified key from config file
    Raises an exception when the key is not present in the config dictionary
    '''
    def readKey(self, key):

        # check if the key exists in the configuration
        if key in self.conf_file.keys():

            # retrieve the value of the key
            val = self.conf_file[key]

            # return the value
            return val

        # otherwise raise an exception
        raise KeyError(f'key {key} not found; in {self.conf_path}')