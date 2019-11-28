import json
import random
import string
import logging
import cv2

from datetime import datetime


#
# CONSTANTS NECESSARY FOR RUNTIME SETUP
#
CONF_PTH = './data/json/config.json'
HUNT_PTH = './data/json/hunts.json'


with open(CONF_PTH, 'r') as conf_file:
    CONF = json.load(conf_file)

with open(HUNT_PTH, 'r') as hunt_file:
    HUNT = json.load(hunt_file)


SCRN_REG = tuple([CONF['screen'][x] for x in ['x','y','width','height']])
SCRN_WDT = CONF['screen']['width']
SCRN_HGT = CONF['screen']['height']

GAME_PTH = CONF['paths']['game']


'''
Function to initalise random user ID if the person running the program
decides to remain anonymous
'''
def user_init():

    global CONF

    chars = string.ascii_uppercase + string.digits
    anon_id = ''.join(random.choice(chars) for _ in range(20))

    CONF['user']['name'] = anon_id

    # save updated config
    with open(CONF_PTH, 'w') as dump_file:
        json.dump(CONF, dump_file, indent=2, separators=(',',':'))

    return anon_id


'''
Helper function for recovering the current patch version the game
is being played on. This is not resistant to people not logging out
of the game for no-downtime patches, but saves a lot of work otherwise.
Requires game installation path to work properly
'''
def get_patch_version():

    # open version file from the specified path
    with open(f'{GAME_PTH}/Version.txt', 'r') as version_file:

        # read the only line in the file
        file_line = version_file.readline()

        # extract patch version
        patch = file_line.split('_')[1].split('-')[1]

        # return the patch
        return patch


'''
Function for retrieving the logger, configured to separately handle
info and error messages
'''
def get_logger(LOG_FORMAT = '%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S',
               LOG_NAME = '',
               LOG_FILE_INFO  = f'./logs/{datetime.today().date()}_scrapless.log',
               LOG_FILE_ERROR = f'./error_logs/{datetime.now().strftime("%d-%m-%d_%H-%M-%S")}_scrapless.err'):
    
    log = logging.getLogger(LOG_NAME)
    log_formatter = logging.Formatter(LOG_FORMAT)

    # comment this to suppress console output
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)
    log.addHandler(stream_handler)

    file_handler_info = logging.FileHandler(LOG_FILE_INFO, mode='w')
    file_handler_info.setFormatter(log_formatter)
    file_handler_info.setLevel(logging.INFO)
    log.addHandler(file_handler_info)

    file_handler_error = logging.FileHandler(LOG_FILE_ERROR, mode='w')
    file_handler_error.setFormatter(log_formatter)
    file_handler_error.setLevel(logging.ERROR)
    log.addHandler(file_handler_error)

    log.setLevel(logging.INFO)

    return log


#
# OTHER CONSTANTS
#
BHMT_LOBBY_SLC = [CONF['behe_lobby'][x] for x in ['height_start','height_end','width_start','width_end']]
BHMT_LOOT_SLC = [CONF['behe_loot'][x] for x in ['height_start','height_end','width_start','width_end']]

GAME_VER = get_patch_version()

LOBBY_SLC = [CONF['lobby_detect'][x] for x in ['height_start','height_end','width_start','width_end']]
LOBBY_IMG = cv2.imread(f'./data/images/targets/lobby_screen/{SCRN_WDT}_{SCRN_HGT}_lobby.png', 0)

LOG = get_logger()

LOOT_SLC = [CONF['loot_detect'][x] for x in ['height_start','height_end','width_start','width_end']]
LOOT_IMG =  cv2.imread(f'./data/images/targets/loot_screen/{SCRN_WDT}_{SCRN_HGT}_loot.png', 0)

HTYPE_SLC = [CONF['htype_detect'][x] for x in ['height_start','height_end','width_start','width_end']]
HTYPE_IMG = cv2.imread(f'./data/images/targets/patrol_screen/{SCRN_WDT}_{SCRN_HGT}_patrol.png', 0)

USER = CONF['user']['name'] if CONF['user']['name'] != "" else user_init()

TESS_PTH = CONF['paths']['tesseract']
TESS_CONF = CONF['paths']['tesseract_conf']

THRT_SLC = [CONF['threat_detect'][x] for x in ['height_start','height_end','width_start','width_end']]

TOKEN_SLC = [CONF['token_detect'][x] for x in ['height_start','height_end','width_start','width_end']]
TOKEN_IMG = cv2.imread(f'./data/images/targets/token/{SCRN_WDT}_{SCRN_HGT}_token.png', 0)












