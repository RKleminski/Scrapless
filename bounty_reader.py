from reader import Reader

'''
Specialised class for reading specifically the bounty screen, and recognising 
its various features
'''
class BountyReader(Reader):

    #
    # CLASS VARIABLES
    #
    # path to folder with screen slices
    SLC_PATH = './data/json/screen/bounty'
    # expected slices to be found
    SLC_CODE = ['draft', 'menu', 'value']

    # path to folder with target images
    TRGT_PATH = './data/targets/bounty'
    # expected targets to be found
    TRGT_CODE = ['draft', 'menu']

    # path to bounty rarity dict
    RARE_PATH = './data/json/bounty/rarity.json'

    def __init__(self):

        # load slices of the screen
        self.slices = self._setSlices(self.SLC_PATH, self.SLC_CODE)

        # load target images of the screen
        self.targets = self._setTargets(self.TRGT_PATH, self.TRGT_CODE)

        # load dictionary of rarity tiers
        self.rarities = self.readFile(self.RARE_PATH)

    '''
    Method for detecting the start of a bounty draft, wraps the detectFromSlice wrapper
    Uses in-class slice and target, with an image input
    Returns a boolean value
    '''
    def detectDraftStart(self, image):

        # return the detection value
        return self.detectFromSlice(image, 'draft')

    '''
    Method for detecting the end of a bounty draft, wraps the detectFromSlice wrapper
    Uses in-class slice and target, with an image input
    Returns a boolean value
    '''
    def detectDraftEnd(self, image):

        # return the detection value
        return self.detectFromSlice(image, 'menu')

    '''
    Method for reading all data off the Draft screen, and checks if it pertainsn to a valid
    bounty tier as defined in configuration files
    In: screenshot of the game screen
    Out:
    '''
    def readScreen(self, image):

        # prepare empty dictionary for data
        data = {}

        # read bounty screen data
        data['value'] = self._readBountyValue(image)
        data['rarity'] = self._readBountyRarity(data['value'])

        # return all read data
        return data

    '''
    Internal function for reading bounty rarity. Raises an exception if the value does not
    exist in the dictionary
    In: integer value data
    Out: string rarity
    '''
    def _readBountyRarity(self, value):

        # check if value in the dictionary
        if value in self.rarities.keys():

            # if so, return rarity
            return self.rarities[value]

        # otherwise raise an exception
        raise ValueError(f'Invalid bounty value of {value}. Retrying...')

    '''
    Internal wrapper method for reading the experience value of a bounty
    In: screenshot of the game lobby
    Out: string bounty value
    '''
    def _readBountyValue(self, image):

        # slice the input image
        image = self.slices['value'].sliceImage(image)

        # launch the reader function
        text = self.readText(image, ocr_config='--psm 13 -c tessedit_char_whitelist=x0123456789',
                            thresh_val=175, scale_x=2, scale_y=2, border_size=5, invert=True, debug=True)

        # skip the first symbol
        text = text[1:]

        # return the read text
        return text