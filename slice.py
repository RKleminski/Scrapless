import os
import json

'''
A class for defining image slices, which store coordinates 
of opposite corners of a rectangle
These slices can also be used to easily return an appropriate 
slice of the image in a numpy array form
'''
class Slice:

    # class variables
    #
    # possible coordinate names
    CORD_LIST = ['height_start', 'height_end', 'width_start', 'width_end']

    '''
    Constructor initalizes the slice with given coordinates
    of the corners that define the span of a rectangular slice
    '''
    def __init__(self, x0 = 0, y0 = 0, x1 = 0 , y1 = 0, json_path = ''):
        
        # if path provided, load coordinates from file
        if json_path != '':
            self._setFromJSON(json_path)
        
        # otherwise, accept them from passed variables
        else:
            self.x0 = x0
            self.y0 = y0

            self.x1 = x1
            self.y1 = y1

    '''
    Function for filling the coordinates from a JSON specification
    file, as provided with the app and used for standardised configuration
    '''
    def _setFromJSON(self, path):

        # check if path is not empty
        if path != '':

            # check if the specified file exists
            if os.path.isfile(path):

                # read the file
                with open(path, 'r') as load_file:

                    # parse JSON to dictionary
                    slice_file = json.load(load_file)

                    # verify all coordinates are in the file
                    for coord in self.CORD_LIST:

                        # raise exception if coordinate not found
                        if coord not in slice_file.keys():
                            raise KeyError(f'key {coord} could not be found in file {path}')

                        # otherwise fill coordinates appropriately
                        self.x0 = slice_file['width_start']
                        self.y0 = slice_file['height_start']
                        self.x1 = slice_file['width_end']
                        self.y1 = slice_file['height_end']

                    # return self
                    return self

            # otherwise raise an exception
            raise FileNotFoundError(f'file {path} could not be found')

        # otherwise raise an exception
        raise ValueError(f'path to a JSON file can\'t be empty')