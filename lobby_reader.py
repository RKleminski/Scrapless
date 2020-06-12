from reader import Reader
from slice import Slice

import cv2

'''
Specialised class for reading specifically the lobby screen, and recognising
its various features
'''
class LobbyReader(Reader):

    #
    # CLASS VARIABLES
    #
    # path to the folder with screen slices
    SLC_PATH = './data/json/screen/lobby'
    # expected slices to be found
    SLC_CODE = ['behemoth', 'detect', 'escalation', 'hunt_type', 'threat']
    
    # path to the folder with target images
    TRGT_PATH = './data/targets/lobby'
    # expected targets to be found
    TRGT_CODE = ['detect', 'hunt_type']
    
    # path to valid hunt file
    HUNT_PATH = './data/json/huntdata/hunts.json'

    # path to hunt tiers
    TIER_PATH = './data/json/huntdata/tiers.json'

    # path to escalation tiers
    ESC_PATH = './data/json/huntdata/escalation_tiers.json'

    # path to elements
    ELEM_PATH = './data/json/huntdata/elements.json'

    def __init__(self):
        
        # load slices of the screen
        self.slices = self._setSlices(self.SLC_PATH, self.SLC_CODE)

        # load target images of the screen
        self.targets = self._setTargets(self.TRGT_PATH, self.TRGT_CODE)

        # load valid hunt dictionary
        self.valid_hunts = self.readFile(self.HUNT_PATH)

        # load hunt tier dictionary
        self.hunt_tiers = self.readFile(self.TIER_PATH)

        # load element array
        self.elements = self._readArrayFile('Elements', self.ELEM_PATH)

        # load escalation tier array
        self.esca_tiers = self._readArrayFile('Tiers', self.ESC_PATH)

        # load escalation names array
        self.escal_names = self._readValidEscas()


    '''
    Method for detecting the relevant screen, wraps the detectFromSlice wrapper
    Uses in-class slice and target, with an image input
    Returns a boolean value
    '''
    def detectScreen(self, image):

        # return the detection value
        return self.detectFromSlice(image, 'detect')

    '''
    Method for reading all data off the lobby screen, and checks if it pertains to a valid
    hunt as defined in configuration files
    In: screenshot of the game screen
    Out: dictionary of values describing the lobby, boolean value of hunt validity
    '''
    def readScreen(self, image):

        # prepare empty dictionary for data
        data = {}

        # read lobby screen data
        data['behemoth'] = self._readBehemoth(image)
        data['escalation'] = self._readEsca(image) if data['behemoth'] == '' else ''
        data['threat'] = self._readThreat(image)
        data['type'] = 'Patrol' if self.detectFromSlice(image, 'hunt_type') else 'Pursuit'
        data['tier'] = data['escalation'] if data['escalation'] != '' else self._readTier(data['threat'])
    
        # check for hunt validity
        self._validateHunt(data)

        # return all read data
        return data

    '''
    Method for reading elements from appropriate JSON file
    In: none
    Out: element string rray
    '''
    def _readArrayFile(self, key, path):

        # read the file
        arr_file = self.readFile(path)

        # read the key out of the file
        value = self.readKey(key, file=arr_file, path=path)

        # return the values
        return value

    '''
    Wrapper method for reading off the slice, launches reader with parametres for behemoth name
    In: screenshot of the game lobby
    Out: behemoth name
    '''
    def _readBehemoth(self, image):

        # slice the input image
        image = self.slices['behemoth'].sliceImage(image)

        # launch the reader function
        text = self.readText(image, ocr_config='./data/tesseract/dauntless', thresh_val=110, 
                            scale_x=6, scale_y=7, border_size=20, invert=True)

        # preprocess the behemoth name
        if_defeat, text = self._processBehemothName(text)

        # fuzzy match the name
        text = self._fuzzyMatch(text, self.valid_hunts.keys(), 80)

        # return the read text
        return text

    '''
    Wrapper method for reading off the slice, launches reader with parametres for escalation name
    In: screenshot of the game lobby
    Out: escalation name
    '''
    def _readEsca(self, image):

        # slice the input image
        image = self.slices['escalation'].sliceImage(image)

        # launch the reader function
        text = self.readText(image, ocr_config='--psm 11', thresh_val=110, speck_size=1,
                            scale_x=6, scale_y=7, border_size=20, invert=True)

        # match the name against allowed escalation names
        text = self._fuzzyMatch(text, self.escal_names, 80)

        return text

    '''
    Wrapper method for reading off the slice, launches it with parametres for reading threat level
    In: screenshot of the game lobby
    Out: hunt threat level
    '''
    def _readThreat(self, image):

        # slice the input image
        image = self.slices['threat'].sliceImage(image)

        # launch the reader function
        text = self.readText(image, ocr_config='--psm 13 -c tessedit_char_whitelist=0123456789',
                            thresh_val=236, speck_size=1, scale_x=4, scale_y=5, border_size=10,
                            invert=True)

        # return read text
        return 0 if text == '' else int(text)

    '''
    Method for reading the hunt tier based on threat level; raises an exception if not found
    In: threat level
    Out: hunt tier
    '''
    def _readTier(self, threat):

        # iterate over tiers present in the file
        for tier_name, tier_range in self.hunt_tiers.items():

            # check if threat in the range
            if threat >= tier_range['lower'] and threat <= tier_range['upper']:

                # return the name of the tier
                return tier_name

        # if no tier was viable, raise an exception
        raise ValueError(f'Invalid threat value of {threat}')

    '''
    Method for reading configuration files and returning valid escalations
    In: none
    Out: array of valid escalation names
    '''
    def _readValidEscas(self):

        # read escalation tier file
        tiers = self.readFile(self.ESC_PATH)['Tiers']

        # combine tiers of escalations with elements
        names = [f'{elem} {tier}' for elem in self.elements for tier in tiers]

        # return the resulting list
        return names

    '''
    Method for validating the hunt data against known, existing hunts
    In: hunt lobby data
    Out: boolean value of validity
    '''
    def _validateHunt(self, data):

        # return validity if lobby is an escalation
        if data['escalation'] != '':
            return True

        # check if behemoth in valid hunts
        elif data['behemoth'] in self.valid_hunts.keys():

            # check if threat matches the behemoth
            if data['threat'] in self.valid_hunts[data['behemoth']] or 'Trial' in data['tier']:

                # if so, return validity
                return True

        # otherwise, raise an exception
        else:
            raise ValueError(f'Invalid hunt detected -- T{data["threat"]} {data["behemoth"]}')