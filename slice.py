from configurable import Configurable

'''
A class for defining image slices, which store coordinates 
of opposite corners of a rectangle
Inherits after Configurable for ease of initialisation
'''
class Slice(Configurable):

    '''
    Constructor initalizes the slice with given coordinates
    of the corners that define the span of a rectangular slice
    '''
    def __init__(self, conf_path):

        # invoke the parent constructor
        Configurable.__init__(self, conf_path)

        # set variable values
        self.x0 = self.readCoord('width_start')
        self.y0 = self.readCoord('height_start')

        self.x1 = self.readCoord('width_end')
        self.y1 = self.readCoord('height_end')

    '''
    A wrapper around the readKey function which additionally checks
    if the read value is a proper coordinate
    '''
    def readCoord(self, key):

        # retrieve coordinate
        coord = self.readKey(key)

        # check if the coordinate is an integer
        if type(coord) == int:

            # check if it has a positive value
            if coord >= 0:

                # return coordinate
                return coord

            # otherwise raise an exception
            raise ValueError(f'screen corrdinates cannot be negative; in {self.conf_path}')

        # otherwise raise an exception
        raise TypeError(f'screen coordinate has to be an integer; in {self.conf_path}')

    '''
    A function which, once an image is provided, isolates the slice out of it
    then returns that section of the image
    In: image in an array form
    Out: a section of input image
    '''
    def sliceImage(self, image):

        # check if the image has of legal size
        for size in image.shape:

            # if any shape is zero, raise an exception
            if size < 1:
                raise ValueError(f'one of image dimensions is lower than 1')

        # slice out the region of the image
        image_slice = image[self.y0:self.y1, self.x0:self.x1, :]

        # return the slice
        return image_slice