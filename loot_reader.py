import re

from itertools import chain

from reader import Reader
from slice import Slice

'''
Specialised class for reading specifically the loot screen, and recognising
its various features
'''
class LootReader(Reader):

    #
    # CLASS VARIABLES
    #
    # path to the folder with screen slices
    SLC_PATH = './data/json/screen/loot'
    # expected slices to be found
    SLC_CODE = ['base_drops', 'behemoth', 'bonus_drops', 'deaths', 'detect', 'elite', 'time', 'trial']

    # path to the folder with screen slices
    TRGT_PATH = './data/targets/loot'
    # expected targets to be found
    TRGT_CODE = ['breaks', 'chest', 'detect', 'elite', 'trial', 'token']

    # path to valid hunt file
    HUNT_PATH = './data/json/huntdata/hunts.json'

    # paths related to item drops
    CELL_PATH = './data/json/drops/cells.json'
    ORBS_PATH = './data/json/drops/orbs.json'
    DROP_PTH = './data/json/drops/behemoth.json'

    # path to OCR confusion dictionary
    CNFS_PATH = './data/json/ocr/confusion.json'

    def __init__(self):
        
        # load slices
        self.slices = self._setSlices(self.SLC_PATH, self.SLC_CODE)

        # load target images
        self.targets = self._setTargets(self.TRGT_PATH, self.TRGT_CODE)

        # load behemoth drops
        self.drops = self.readFile(self.DROP_PTH)

        # load orbs
        self.orbs = self.readFile(self.ORBS_PATH)

        # load cell names
        self.cells = self.readFile(self.CELL_PATH)

        # load OCR confusion
        self.ocr_confuse = self.readFile(self.CNFS_PATH)

        # load vocabulary of valid words to appear among behemoth names
        self.behe_vocab = list(self.readFile(self.HUNT_PATH).keys())
        self.behe_vocab.extend(['Defeated', 'Patrol'])

    '''
    Method for detecting the relevant screen, wraps the detectFromSlice wrapper
    Uses in-class slice and target, with an image output
    Returns a boolean value
    '''
    def detectLootScreen(self, image):

        # return the detection value
        return self.detectFromSlice(image, 'detect')

    '''
    Wrapper method for detecting the trial end screen using detectFromSlice
    Uses in-class slice and targeg
    In: image of the loot screen
    Out: boolean value
    '''
    def detectTrialEnd(self, image):

        # return the detection value
        return self.detectFromSlice(image, 'trial')

    '''
    Method for reading basic data off the loot screen; these are not the actual drops
    In: screenshot of the game screen
    Out: dictionary of values describing the loot screen
    '''
    def readScreen(self, image):

        # prepare empty dictionary for data
        data = {}

        # read lobby screen data
        data['defeat'], data['behemoth'] = self._readBehemoth(image)
        data['elite'] = self._detectElite(image)
        data['deaths'] = self._readDeaths(image)
        data['time'] = self._readTime(image)

        # return all read data
        return data

    '''
    Method for reading full loot data off the screen, ie. all items dropped from the behemoth
    In: image of the loot screen
    Out: array of dictionary objects describing loot
    '''
    def readLoot(self, image, behemoth):

        # find location of part break section
        breaks_img = self.slices['base_drops'].sliceImage(image)
        if_breaks, breaks_xy = self.detectElement(breaks_img, self.targets['breaks'])

        # find location of patrol bonus section
        chest_img = self.slices['bonus_drops'].sliceImage(image)
        if_chest, chest_xy = self.detectElement(chest_img, self.targets['chest'])

        # modify base drops slice accordingly
        if if_breaks:
            base_slice = self.slices['base_drops']
            base_slice.y1 = base_slice.y0 + breaks_xy[1]
        else:
            base_slice = self.slices['base_drops']

        # modify bonus drops slice accordingly
        if if_chest:
            bonus_slice = self.slices['bonus_drops']
            bonus_slice.y1 = bonus_slice.y0 + chest_xy[1]
        else:
            bonus_slice = self.slices['bonus_drops']

        # get base drops
        base_img = base_slice.sliceImage(image)
        base_data = self._readLootSlice(base_img)

        # get bonus drops
        bonus_img = self.slices['bonus_drops'].sliceImage(image)
        bonus_data = self._readLootSlice(bonus_img)

        # test drop processing
        base_data = [self._processLootLine(line, behemoth) for line in base_data if line != '']
        bonus_data = [self._processLootLine(line, behemoth) for line in bonus_data if line != '']

        # clear of empty lines
        base_data = list(chain.from_iterable(base_data))
        bonus_data = list(chain.from_iterable(bonus_data))

        # return the merger of this data
        return [*base_data, *bonus_data]

    '''
    Method for detecting if the user owns an Elite Hunt Pass
    In: screenshot of the loot screen
    Out: boolean value
    '''
    def _detectElite(self, image):

        # return the detection value
        return self.detectFromSlice(image, 'elite', prec=0.95)

    '''
    Internal method for processing the drop count
    In: line of count
    Out: actual drop count integer
    '''
    def _processDropCount(self, line):

        # skip the first character in the string
        drop_count = line[1:]

        # apply replacement of symbols that OCR tends to get wrong
        for mistake in self.ocr_confuse.keys():
            drop_count = drop_count.replace(mistake, self.ocr_confuse[mistake])

        # return the count
        return int(drop_count)

    '''
    Internal method for processing non-cell drop line
    In: loot text line, behemoth name
    Out: drop data
    '''
    def _processDropLine(self, line, behemoth):

        # empty dict for things
        line_data = {}

        # match to a behemoth drop first
        line_data['name'] = self._fuzzyMatch(line, self.drops[behemoth].keys(), score_threshold=80)

        # if we have a match
        if line_data['name'] != '':

            # add rarity
            line_data['rarity'] = self.drops[behemoth][line_data['name']]

        # otheriwse check in orbs
        else:

            # attempt to match with an orb
            line_data['name'] = self._fuzzyMatch(line, self.orbs.keys(), score_threshold=80)

            # if we have a match
            if line_data['name'] != '':

                # add rarity
                line_data['rarity'] = self.orbs[line_data['name']]

        # return drop name as found (or not)
        return line_data if line_data['name'] != '' else {}

    '''
    Internal method for processing the cell name
    In: loot text line
    Out: cell drop name
    '''
    def _processCellLine(self, line):

        # cut the line further
        cell_grade = line.split(' ', 1)[0]

        # cut out the grade from the name
        cell_name = line.split(' ', 1)[-1]
        
        # cut out the 'Cell' from the name
        cell_name = cell_name.split(' ')[:-1]

        # turn cell name back into a string
        cell_name = ' '.join(cell_name)

        # fuzzy match cell name
        cell_name = self._fuzzyMatch(cell_name, self.cells.keys(), score_threshold=80)

        if cell_name == '':
            return {}
        else:
            return {'name': f'{cell_grade} {cell_name} Cell',
                    'rarity': 'Rare (Cell)' if cell_grade == '+2' else 'Uncommon (Cell)'
                    }

    '''
    Internal method for processing each line of text. Returns a proper drop or empty string
    In: line of loot text
    Out: empty string or a drop string
    '''
    def _processLootLine(self, line, behemoth):

        # ensure the line is a text-line
        if re.search('[a-zA-Z]', line):

            # acquire drop's name
            drop_name = line.split(' ', 1)[-1]

            # fuzzy match differently depending if this is a cell
            # check for any of the listed strings, for fine-grained control against
            # OCR mistakes
            if any(x in drop_name for x in ['Call', 'Cell']):
                drop_data = self._processCellLine(drop_name)
            else:
                drop_data = self._processDropLine(drop_name, behemoth)

            # if a name found
            if len(drop_data) > 0:

                # acquire drop count
                drop_count = line.split(' ', 1)[0]
                
                # process and clean the count up
                drop_count = self._processDropCount(drop_count)

                # add count to data
                drop_data['count'] = drop_count

                # return the data
                return self._splitDrop(drop_data)

            # otherwise return empty
            else:
                return []

        # if not, return empty
        else:
            return []

    '''
    Method for reading the behemoth name and fuzzy-matching it to possible names
    In: screenshot of the loot screen
    Out: behemoth name
    '''
    def _readBehemoth(self, image):

        # slice the input image
        image = self.slices['behemoth'].sliceImage(image)

        # launch the reader function
        text = self.readText(image, ocr_config='./data/tesseract/dauntless', thresh_val=100, 
                            scale_x=6, scale_y=7, border_size=20, invert=True)

        # preprocess the behemoth name
        if_defeat, text = self._processBehemothName(text)

        # fuzzy match the name
        text = self._fuzzyMatch(text, self.drops.keys(), 80)

        # return the read text
        return if_defeat, text

    '''
    Method for reading the text informing about bonus drops; determines death count 
    based on that message
    In: screenshot of the loot screen
    Out: integer number of deaths
    '''
    def _readDeaths(self, image):

        # slice the input image
        image = self.slices['deaths'].sliceImage(image)

        # launch the reader function
        text = self.readText(image, ocr_config='--psm 13', thresh_val=150, speck_size=1,
                            scale_x=1, scale_y=1, border_size=10, invert=True)

        # lowercase the text
        text = text.lower()

        # get the number of deaths based on the bonus text
        text = 0 if 'never' in text else 1 if 'once' in text else 2 if 'twice' in text else 3 

        # return the deaths
        return text

    '''
    Internal method for reading all loot drops from a given slice of the screen
    In: screen slice
    Out: an array of dictionary loot entries
    '''
    def _readLootSlice(self, image, debug=False):

        # read all text from the slice
        lines = self.readText(image, ocr_config='--psm 11', thresh_val=120, speck_size=1,
                            scale_x=4, scale_y=5, border_size=10, invert=True, debug=debug)

        # return the lines
        return lines.splitlines()

    '''
    Method for reading the hunt time
    In: screenshot of the loot screen
    Out: integer number of deaths
    '''
    def _readTime(self, image):

        # slice the input image
        image = self.slices['time'].sliceImage(image)

        # launch the reader function
        text = self.readText(image, ocr_config='--psm 13 -c tessedit_char_whitelist=0123456789:.',
                            thresh_val=150, speck_size=1, scale_x=4, scale_y=5, border_size=20, invert=True)

        # return the value
        return text

    '''
    Internal method for splitting the drops appearing in a single line, according to
    their rarity
    In: drop data dict
    Out: array of drop datas
    '''
    def _splitDrop(self, drop_data):

        # retrieve drop count from line
        line_count = drop_data['count']

        # determine per-roll drop count
        drop_count = 2 if drop_data['rarity'] == 'Epic' else 3 if 'Orb' in drop_data['rarity'] else 1

        # replace count appearing in line with a proper count
        drop_data['count'] = drop_count

        # if there are ten or more drops in a stack
        if line_count >= 10:

            # if we are dealing with an orb
            if 'Orb' in drop_data['rarity']:

                # pre-process the line count to account for base 10 drop in patrols
                line_count = (line_count - 10) if (line_count >= 10 and line_count % 3 != 0) else line_count

            # otherwise, this is a possible error in OCR
            else:
                raise ValueError(f'Suspiciously big stack of loot. Screenshot saved. Data will not be read')

        # return drop data multiplied by how many rows we really need here
        return [ drop_data ] * int(line_count / drop_count)