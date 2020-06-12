import os
import cv2
import pytesseract
import numpy as np

from fuzzywuzzy import fuzz, process
from slice import Slice
from configurable import Configurable

'''
Generic class capable of reading the screen
Provides a method for detecting an element in a given image slice
And for reading a string of text off a given image slice
Intended as a base class to be inherited from by the more advanced readers

---

Inherits after Configurable to grant access to readFile
'''
class Reader(Configurable):

    # constructor existing for the sake of placeholding
    def __init__(self):
        
        self.slices = {}
        self.targets = {}

    '''
    Generic method for detecting an element on the screen slice
    Expects an image, target image and expected precision
    Returns boolean value indicating if element was detected, and the location
    of maximum detection value
    '''
    def detectElement(self, image, target, prec=0.8):

        # convert the input image to grayscale for better detection
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # match target template to the image
        result = cv2.matchTemplate(image, target, cv2.TM_CCOEFF_NORMED)

        # retrieve the minimum and maximum detection value, and their locations
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # if the matching reached desired precision at any location, return true
        if max_val < prec:
            return False, max_loc
        return True, max_loc

    '''
    Method for wrapping operations necessary to detect an element in a slice
    In: screenshot of the game lobby
    Out: boolean detection value
    '''
    def detectFromSlice(self, image, slice_name, prec=0.8):

        # slice the input image
        image = self.slices[slice_name].sliceImage(image)

        # call the parent method for detecting element
        detected, loc = self.detectElement(image, self.targets[slice_name], prec=prec)

        # return the detection value
        return detected

    '''
    Generic method for reading text on the screen slice
    Contains multiple arguments to proper put the image trough extensive pre-processing
    which includes possible thresholding, inverting the colours, scaling the image, trimming
    white border around the image and removing pixel-specks that occur on the images
    '''
    def readText(self, image, ocr_config, thresh_val, 
                speck_size = 1, scale_x = 1, scale_y = 1, 
                border_size = 100, shrink_border = 5, 
                invert = False, debug=False):

        # convert the input image to grayscale for better reading
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # threshold the image to prepare it for OCR reading
        ret, image = cv2.threshold(image, thresh_val, 255, cv2.THRESH_BINARY)

        # filter out unexpected pixel speckles
        cv2.filterSpeckles(image, 0, speck_size, speck_size)

        # invert image colours if necessary
        if invert:
            image = cv2.bitwise_not(image)

        # compute the new dimensions for the image to counteract small natural dimensions
        width = image.shape[1] * scale_x
        height = image.shape[0] * scale_y

        # re-scale the image
        image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)

        # trim the white border from around the image, to increase OCR quality
        image = self._trimBorder(image, border_size, shrink_border)

        if debug:
            cv2.imwrite('./debug_data/debug_text.png', image)

        # call PyTesseract reader function and return the found text
        return pytesseract.image_to_string(image, lang='eng', config=ocr_config)

    '''
    Method for fuzzy matching a string against possible strings
    In: string, list of allowed strings, score threshold for similarity
    Out: the best match found, or empty string if not met the threshold
    '''
    def _fuzzyMatch(self, string, allowed_strings, score_threshold):

        # check if the string is an exact match; if so, return
        if string in allowed_strings:
            return string

        # otherwise perform a fuzzy match
        else:
            match = process.extractOne(string, allowed_strings, scorer=fuzz.ratio, score_cutoff=score_threshold)

            # return empty string if no matches, or a match if one exists
            return '' if match is None else match[0]

    '''
    A method for trimming down behemoth text line down to basic form.
    In: a line of text with behemoth name
    Out: name trimmed to basic form, boolean indicator of defeat
    '''
    def _processBehemothName(self, text):

        # reduce to one line, remove heroic classifier, 
        # remove patrol classifier, trim trailing whitespaces
        text = text.replace('\n', '').replace('(Heroic)', '').replace('Patrol', '').strip()

        # split text into an array
        text_arr = text.split(' ')
        
        # determine defeat
        if_defeat = text_arr[0] == 'Defeated'

        # retrieve the actual name
        behemoth = text_arr[-1]

        # return values
        return if_defeat, behemoth

    '''
    Method for reading in screen slices
    Uses the internally stored path to the folder containing JSON files
    Returns a dictionary of Slices instantiated using those
    '''
    def _setSlices(self, path, codes):

        # prepare empty dictionary
        slice_dict = {}

        # iterate over the expected slice spec files
        for slice_name in codes:

            # construct a path to slice file
            slice_path = f'{path}/{slice_name}.json'

            # add slice to the dictionary under the appropriate key
            slice_dict[slice_name] = Slice(slice_path)

        # return the dictionary of slices
        return slice_dict

    '''
    Method for reading in screen target images
    Uses the internally stored path to the folder containing JSON files
    Returns a dictionary of target images
    '''
    def _setTargets(self, path, codes):

        # prepare empty dictionary
        target_dict = {}

        # iterate over the expected image files
        for target_name in codes:

            # construct a path to target file
            target_path = f'{path}/{target_name}.png'

            # check if file exists
            if os.path.isfile(target_path):

                # read the image file and add it to the dictionary
                target_dict[target_name] = cv2.imread(target_path, 0)

            # otherwise raise an exception
            else:
                raise FileNotFoundError(f'file {target_path} is not a file or could not be read')

        # if no exceptions occured, return the dict
        return target_dict

    '''
    A function that, given an image and border thickness parametre,
    will remove the pure white space around the processed image, 
    then return the result.
    Should the resulting image be trimmed to the point of becoming invalid, 
    eg. just a singular point, the method will slightly reduce desired border 
    size and attempt again, until a valid image is created 
    '''
    def _trimBorder(self, image, border, shrink = 5):

        # perform initial trimming
        trim_image = self._trimWhite(image, border)

        # progressibely reduce size of white border if it causes invalid image to be created
        while (trim_image.shape[0] == 0 or trim_image.shape[1] == 0):
            border -= shrink
            trim_image = self._trimWhite(image, border)

        # if the image is valid, return it
        return trim_image

    '''
    Helper function performing a single step of trimming the white border
    of an image. Intended not to be used outside of its iterative parent method
    _trimBorder
    '''
    def _trimWhite(self, image, border):

        # negate the image bit-wise
        bit = cv2.bitwise_not(image)

        # get the non-zero coordinates
        nonzero = np.nonzero(bit)

        # if there are such coordinates, get the min and max points
        if bit.any():
            minx = min(nonzero[1])
            maxx = max(nonzero[1])

            miny = min(nonzero[0])
            maxy = max(nonzero[0])

            # crop the image while keeping a slight border around it
            image = image[(miny-border):(maxy+border),(minx-border):(maxx+border)].copy()

        # return the input image
        return image