import json
import random
import string
import logging
import cv2
import sys
import os

from datetime import datetime
from uuid import uuid4

scrap_ver = '0.9.8.1'

'''
Function for retrieving the logger, configured to separately handle
info and error messages
'''
def get_logger(LOG_FORMAT = '%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S',
               LOG_NAME = '',
               LOG_FILE_INFO  = f'./logs/{datetime.today().date()}_scrapless.log',
               LOG_FILE_ERROR = f'./error_logs/{datetime.today().date()}_scrapless.err'):
    
    log = logging.getLogger(LOG_NAME)
    log_formatter = logging.Formatter(LOG_FORMAT)

    # comment this to suppress console output
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)
    log.addHandler(stream_handler)

    file_handler_info = logging.FileHandler(LOG_FILE_INFO, mode='a')
    file_handler_info.setFormatter(log_formatter)
    file_handler_info.setLevel(logging.INFO)
    log.addHandler(file_handler_info)

    file_handler_error = logging.FileHandler(LOG_FILE_ERROR, mode='a')
    file_handler_error.setFormatter(log_formatter)
    file_handler_error.setLevel(logging.ERROR)
    #log.addHandler(file_handler_error)

    log.setLevel(logging.INFO)

    return log


'''
Function to initalise random user ID if the person running the program
decides to remain anonymous
'''
def user_init():

    global CONF

    LOG.info('SETUP: No username found, generating a random user ID.')

    anon_id = uuid4()

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

# ====================
# FOLDER CREATION
# ====================
#
path = './logs'
if not os.path.exists(path):
    os.makedirs(path)

path = './error_logs'
if not os.path.exists(path):
    os.makedirs(path)

# ====================
# SETTING UP LOGGER
# ====================
#
LOG = get_logger()


# ====================
# WELCOME MESSAGE
# ====================
#
welcome_string = f'=== WELCOME TO SCRAPLESS {scrap_ver} ! ==='
print('=' * len(welcome_string))
print(welcome_string)
print('=' * len(welcome_string))
print('\n')


# ====================
# READING CONFIG FILE
# ====================
#
try:
    CONF_PTH = './data/json/config.json'

    with open(CONF_PTH, 'r') as conf_file:
        CONF = json.load(conf_file)

    LOG.info('SETUP: Config file read successfully.')

except Exception:
    LOG.Exception('An exception occured while reading the config.json file: ')
    sys.exit(1)


# ====================
# READING VALID HUNTS
# ====================
#
try:
    HUNT_PTH = './data/json/hunts.json'

    # read file of allowed hunts
    with open(HUNT_PTH, 'r') as hunt_file:
        HUNT = json.load(hunt_file)

    ELEMENTS = ['Blaze', 'Frost', 'Shock', 'Terra', 'Neutral', 'Umbral', 'Radiant']
    ESCAL_TIERS = [f'{elem} {tier}' for elem in ELEMENTS for tier in ['Escalation 1-13', 'Escalation 10-50']]

    LOG.info('SETUP: Valid hunt references loaded.')

except Exception:
    LOG.exception('An error occured while reading the hunts.json file: ')
    sys.exit(1)


# ====================
# READING VALID UNIVERSAL DROPS
# ====================
#
try:
    UDROPS_PTH = './data/json/universal_drops.json'

    # read file of allowed hunts
    with open(UDROPS_PTH, 'r') as udrop_file:
        ORB_LIST = json.load(udrop_file)['Orbs']
    with open(UDROPS_PTH, 'r') as udrop_file:
        CELL_LIST = json.load(udrop_file)['Cells']

    LOG.info('SETUP: Valid universal drops references loaded.')

except Exception:
    LOG.exception('An error occured while reading the universal_drops.json file: ')
    sys.exit(1)


# ====================
# READING CONFUSION DICT
# ====================
#
try:
    CONFUSION_PTH = './data/json/confusion.json'

    # read file of allowed hunts
    with open(CONFUSION_PTH, 'r') as confusion_file:
        CONFUSION_DICT = json.load(confusion_file)

    LOG.info('SETUP: OCR character confusion dictionary loaded.')

except Exception:
    LOG.exception('An error occured while reading the confusion.json file: ')
    sys.exit(1)



# ====================
# READING HUNT DROPS
# ====================
#
try:
    DROP_PTH = './data/json/behemoth_drops.json'

    # read file of allowed hunts
    with open(DROP_PTH, 'r') as drop_file:
        DROP_LIST = json.load(drop_file)

    LOG.info('SETUP: Valid hun drop lists loaded.')

except Exception:
    LOG.exception('An error occured while reading the drop_list.json file: ')
    sys.exit(1)


# ====================
# GAME AND TESSERACT PATHS
# ====================
#
try:
    GAME_PTH = CONF['paths']['game']
    TESS_PTH = CONF['paths']['tesseract']
    TESS_CONF = CONF['paths']['tesseract_conf']

    LOG.info('SETUP: Game and Tesseract paths loaded.')

except Exception:
    LOG.exception('An error occured while reading Game and Tesseract paths: ')
    sys.exit(1)


# ====================
# SCREEN SPECIFICATION READING
# ====================
#
try:
    SCRN_REG = tuple([CONF['screen'][x] for x in ['x_offset','y_offset','width','height']])
    SCRN_WDT = CONF['screen']['width']
    SCRN_HGT = CONF['screen']['height']

    Y_SCALE = 1
    X_SCALE = 1

    A_RATIO = ''

    if SCRN_WDT/SCRN_HGT == 16/10:
        A_RATIO = '16:10'
        X_SCALE = SCRN_WDT / 1680
        Y_SCALE = SCRN_HGT / 1050

    elif SCRN_WDT/SCRN_HGT == 16/9:
        A_RATIO = '16:9'
        X_SCALE = SCRN_WDT / 1920
        Y_SCALE = SCRN_HGT / 1080

    else:
        A_RATIO = f'{SCRN_WDT}:{SCRN_HGT}'

    A_RATIO_PATH = A_RATIO.replace(':','_')

    LOG.info(f'SETUP: Screen specifications found, {SCRN_WDT}x{SCRN_HGT}p resolution, {A_RATIO} aspect ratio.')

except Exception:
    LOG.exception('An error occured while establishing screen specifications: ')
    sys.exit(1)


# ====================
# ESTABLISH USER NAME
# ====================
#
try:
    USER = CONF['user']['name'] if CONF['user']['name'] != "" else user_init()
    LOG.info(f'SETUP: Username set to {USER}')

except Exception:
    LOG.exception('An error occured when establishing username: ')
    sys.exit(1)


# ====================
# READ PATCH VERSION
# ====================
#
try:
    GAME_VER = get_patch_version()
    LOG.info(f'SETUP: Game version {GAME_VER} detected.')

except Exception:
    LOG.exception('An error occured when retrieving patch version: ')
    sys.exit(1)


# ====================
# READ ASPECT RATIO CONFIG
# ====================
#
try:
    ASP_CONF_PTH = f'./data/json/{A_RATIO.replace(":","_")}_config.json'

    with open(ASP_CONF_PTH, 'r') as conf_file:
        ASP_CONF = json.load(conf_file)

    LOG.info(f'SETUP: Config file for {A_RATIO} ratio accessed successfully.')

except Exception:
    LOG.exception(f'An error has occured when opening config file for {A_RATIO} raio: ')
    sys.exit(1)


# ====================
# LOBBY CONFIG READ
# ====================
#
try:

    BHMT_LOBBY_SLC = [int(ASP_CONF['lobby']['behemoth_slice']['height_start'] * Y_SCALE),
                  int(ASP_CONF['lobby']['behemoth_slice']['height_end'] * Y_SCALE),
                  int(ASP_CONF['lobby']['behemoth_slice']['width_start'] * X_SCALE),
                  int(ASP_CONF['lobby']['behemoth_slice']['width_end'] * X_SCALE)]


    LOBBY_SLC = [int(ASP_CONF['lobby']['slice']['height_start'] * Y_SCALE),
             int(ASP_CONF['lobby']['slice']['height_end'] * Y_SCALE),
             int(ASP_CONF['lobby']['slice']['width_start'] * X_SCALE),
             int(ASP_CONF['lobby']['slice']['width_end'] * X_SCALE)]


    LOBBY_IMG = cv2.imread(f'./data/targets/lobby_screen/{A_RATIO_PATH}.png', 0)
    new_size = ( int(LOBBY_IMG.shape[1] * X_SCALE),  int(LOBBY_IMG.shape[0] * Y_SCALE))
    LOBBY_IMG = cv2.resize(LOBBY_IMG, new_size)


    HTYPE_SLC = [int(ASP_CONF['lobby']['hunt_type_slice']['height_start'] * Y_SCALE),
             int(ASP_CONF['lobby']['hunt_type_slice']['height_end'] * Y_SCALE),
             int(ASP_CONF['lobby']['hunt_type_slice']['width_start'] * X_SCALE),
             int(ASP_CONF['lobby']['hunt_type_slice']['width_end'] * X_SCALE)]


    HTYPE_IMG = cv2.imread(f'./data/targets/patrol_screen/{A_RATIO_PATH}.png', 0)
    new_size = ( int(HTYPE_IMG.shape[1] * X_SCALE),  int(HTYPE_IMG.shape[0] * Y_SCALE))
    HTYPE_IMG = cv2.resize(HTYPE_IMG, new_size)


    THRT_SLC = [int(ASP_CONF['lobby']['threat_slice']['height_start'] * Y_SCALE),
                int(ASP_CONF['lobby']['threat_slice']['height_end'] * Y_SCALE),
                int(ASP_CONF['lobby']['threat_slice']['width_start'] * X_SCALE),
                int(ASP_CONF['lobby']['threat_slice']['width_end'] * X_SCALE)]


    LOG.info('Lobby recognition configuration loaded successfully.')

except Exception:
    LOG.exception('An error has occured while reading the LOBBY section of the config: ')
    sys.exit(1)


# ====================
# LOOT CONFIG READ
# ====================
#
try:

    LOOT_BHMT_SLC = [int(ASP_CONF['loot']['behemoth_slice']['height_start'] * Y_SCALE),
                    int(ASP_CONF['loot']['behemoth_slice']['height_end'] * Y_SCALE),
                    int(ASP_CONF['loot']['behemoth_slice']['width_start'] * X_SCALE),
                    int(ASP_CONF['loot']['behemoth_slice']['width_end'] * X_SCALE)]


    LOOT_SLC = [int(ASP_CONF['loot']['slice']['height_start'] * Y_SCALE),
            int(ASP_CONF['loot']['slice']['height_end'] * Y_SCALE),
            int(ASP_CONF['loot']['slice']['width_start'] * X_SCALE),
            int(ASP_CONF['loot']['slice']['width_end'] * X_SCALE)]


    LOOT_IMG =  cv2.imread(f'./data/targets/loot_screen/{A_RATIO_PATH}.png', 0)
    new_size = ( int(LOOT_IMG.shape[1] * X_SCALE),  int(LOOT_IMG.shape[0] * Y_SCALE))
    LOOT_IMG = cv2.resize(LOOT_IMG, new_size)

    BREAK_IMG = cv2.imread(f'./data/targets/break_parts/{A_RATIO_PATH}.png', 0)
    new_size = ( int(BREAK_IMG.shape[1] * X_SCALE),  int(BREAK_IMG.shape[0] * Y_SCALE))
    BREAK_IMG = cv2.resize(BREAK_IMG, new_size)

    ELITE_IMG = cv2.imread(f'./data/targets/elite_pass/{A_RATIO_PATH}.png', 0)
    new_size = ( int(ELITE_IMG.shape[1] * X_SCALE),  int(ELITE_IMG.shape[0] * Y_SCALE))
    ELITE_IMG = cv2.resize(ELITE_IMG, new_size)

    LOOT_TIME_SLC = [int(ASP_CONF['loot']['time_slice']['height_start'] * Y_SCALE),
            int(ASP_CONF['loot']['time_slice']['height_end'] * Y_SCALE),
            int(ASP_CONF['loot']['time_slice']['width_start'] * X_SCALE),
            int(ASP_CONF['loot']['time_slice']['width_end'] * X_SCALE)]

    LOOT_DEATH_SLC = [int(ASP_CONF['loot']['death_slice']['height_start'] * Y_SCALE),
            int(ASP_CONF['loot']['death_slice']['height_end'] * Y_SCALE),
            int(ASP_CONF['loot']['death_slice']['width_start'] * X_SCALE),
            int(ASP_CONF['loot']['death_slice']['width_end'] * X_SCALE)]

    LOOT_ELITE_SLC = [int(ASP_CONF['loot']['elite_slice']['height_start'] * Y_SCALE),
            int(ASP_CONF['loot']['elite_slice']['height_end'] * Y_SCALE),
            int(ASP_CONF['loot']['elite_slice']['width_start'] * X_SCALE),
            int(ASP_CONF['loot']['elite_slice']['width_end'] * X_SCALE)]

    LOOT_BASE_SLC = [int(ASP_CONF['loot']['base_drop_slice']['height_start'] * Y_SCALE),
                int(ASP_CONF['loot']['base_drop_slice']['height_end'] * Y_SCALE),
                int(ASP_CONF['loot']['base_drop_slice']['width_start'] * X_SCALE),
                int(ASP_CONF['loot']['base_drop_slice']['width_end'] * X_SCALE)]

    LOOT_BONS_SLC = [int(ASP_CONF['loot']['bonus_drop_slice']['height_start'] * Y_SCALE),
                int(ASP_CONF['loot']['bonus_drop_slice']['height_end'] * Y_SCALE),
                int(ASP_CONF['loot']['bonus_drop_slice']['width_start'] * X_SCALE),
                int(ASP_CONF['loot']['bonus_drop_slice']['width_end'] * X_SCALE)]

    LOG.info('Loot recognition configuration loaded successfully.')

except Exception:
    LOG.exception('An error has occured while reading the LOOT section of the config: ')
    sys.exit(1)


# ====================
# BOUNTY CONFIG READ
# ====================
#
try:

    BOUNTY_DRAFT_SLC = [int(ASP_CONF['bounty']['draft_slice']['height_start'] * Y_SCALE),
                        int(ASP_CONF['bounty']['draft_slice']['height_end'] * Y_SCALE),
                        int(ASP_CONF['bounty']['draft_slice']['width_start'] * X_SCALE),
                        int(ASP_CONF['bounty']['draft_slice']['width_end'] * X_SCALE)]


    BOUNTY_VAL_SLC = [int(ASP_CONF['bounty']['value_slice']['height_start'] * Y_SCALE),
                    int(ASP_CONF['bounty']['value_slice']['height_end'] * Y_SCALE),
                    int(ASP_CONF['bounty']['value_slice']['width_start'] * X_SCALE),
                    int(ASP_CONF['bounty']['value_slice']['width_end'] * X_SCALE)]


    BOUNTY_MENU_SLC = [int(ASP_CONF['bounty']['menu_slice']['height_start'] * Y_SCALE),
                        int(ASP_CONF['bounty']['menu_slice']['height_end'] * Y_SCALE),
                        int(ASP_CONF['bounty']['menu_slice']['width_start'] * X_SCALE),
                        int(ASP_CONF['bounty']['menu_slice']['width_end'] * X_SCALE)]


    BOUNTY_DRAFT_IMG = cv2.imread(f'./data/targets/bounty_draft/{A_RATIO_PATH}.png', 0)
    new_size = ( int(BOUNTY_DRAFT_IMG.shape[1] * X_SCALE),  int(BOUNTY_DRAFT_IMG.shape[0] * Y_SCALE))
    BOUNTY_DRAFT_IMG = cv2.resize(BOUNTY_DRAFT_IMG, new_size)


    BOUNTY_MENU_IMG = cv2.imread(f'./data/targets/bounty_menu/{A_RATIO_PATH}.png', 0)
    new_size = ( int(BOUNTY_MENU_IMG.shape[1] * X_SCALE),  int(BOUNTY_MENU_IMG.shape[0] * Y_SCALE))
    BOUNTY_MENU_IMG = cv2.resize(BOUNTY_MENU_IMG, new_size)


    LOG.info('Bounty draft recognition configuration loaded successfully.')

except Exception: 
    LOG.exception('An error has occured while reading the BOUNTY section of the config.')
    sys.exit(1)


# ====================
# TRIAL CONFIG READ
# ====================
#
try:

    TRIAL_RES_SLC = [int(ASP_CONF['trial']['result_slice']['height_start'] * Y_SCALE),
                    int(ASP_CONF['trial']['result_slice']['height_end'] * Y_SCALE),
                    int(ASP_CONF['trial']['result_slice']['width_start'] * X_SCALE),
                    int(ASP_CONF['trial']['result_slice']['width_end'] * X_SCALE)]


    BHMT_TRIAL_SLC = [int(ASP_CONF['trial']['behemoth_slice']['height_start'] * Y_SCALE),
                    int(ASP_CONF['trial']['behemoth_slice']['height_end'] * Y_SCALE),
                    int(ASP_CONF['trial']['behemoth_slice']['width_start'] * X_SCALE),
                    int(ASP_CONF['trial']['behemoth_slice']['width_end'] * X_SCALE)]
                    

    TRIAL_RES_IMG = cv2.imread(f'./data/targets/trial_result/{A_RATIO_PATH}.png', 0)
    new_size = ( int(TRIAL_RES_IMG.shape[1] * X_SCALE),  int(TRIAL_RES_IMG.shape[0] * Y_SCALE))
    TRIAL_RES_IMG = cv2.resize(TRIAL_RES_IMG, new_size)


except Exception:
    LOG.exception('An error has occured while reading the TRIAL section of the config')
    sys.exit(1)


# ====================
# ESCALATION CONFIG READ
# ====================
#
try:

    ESCAL_LOBBY_SLC = [int(ASP_CONF['escalation']['lobby_slice']['height_start'] * Y_SCALE),
                  int(ASP_CONF['escalation']['lobby_slice']['height_end'] * Y_SCALE),
                  int(ASP_CONF['escalation']['lobby_slice']['width_start'] * X_SCALE),
                  int(ASP_CONF['escalation']['lobby_slice']['width_end'] * X_SCALE)]


    ESCAL_RANK_SLC_13 = [int(ASP_CONF['escalation']['rank_slice_13']['height_start'] * Y_SCALE),
                    int(ASP_CONF['escalation']['rank_slice_13']['height_end'] * Y_SCALE),
                    int(ASP_CONF['escalation']['rank_slice_13']['width_start'] * X_SCALE),
                    int(ASP_CONF['escalation']['rank_slice_13']['width_end'] * X_SCALE)]


    ESCAL_RANK_SLC_50 = [int(ASP_CONF['escalation']['rank_slice_50']['height_start'] * Y_SCALE),
                    int(ASP_CONF['escalation']['rank_slice_50']['height_end'] * Y_SCALE),
                    int(ASP_CONF['escalation']['rank_slice_50']['width_start'] * X_SCALE),
                    int(ASP_CONF['escalation']['rank_slice_50']['width_end'] * X_SCALE)]


    ESCAL_SUMM_SLC = [int(ASP_CONF['escalation']['summary_slice']['height_start'] * Y_SCALE),
                    int(ASP_CONF['escalation']['summary_slice']['height_end'] * Y_SCALE),
                    int(ASP_CONF['escalation']['summary_slice']['width_start'] * X_SCALE),
                    int(ASP_CONF['escalation']['summary_slice']['width_end'] * X_SCALE)]


    LOG.info('Escalation recognition configuation loaded successfully.')

except Exception:
    LOG.exception('An error has occured while reading the ESCALATION section of the config: ')
    sys.exit(1)


# ====================
# OVERLAY CONFIG READ
# ====================
#
try:

    OVERLAY_ON = CONF['overlay']['enable'] == 'Yes'
    OVERLAY_OPACITY = float(CONF['overlay']['opacity']) / 100.0

    OVERLAY_X = CONF['overlay']['position']['X']
    OVERLAY_Y = CONF['overlay']['position']['Y']

    OVERLAY_MAX_LINES = CONF['overlay']['output']['max_lines']
    OVERLAY_FONT = CONF['overlay']['output']['font']
    OVERLAY_FONT_SIZE = str(CONF['overlay']['output']['font-size'])

    OVERLAY_COLOR_BG = CONF['overlay']['colors']['background']
    OVERLAY_COLOR_SUCCESS = CONF['overlay']['colors']['success']
    OVERLAY_COLOR_INFO = CONF['overlay']['colors']['info']
    OVERLAY_COLOR_WARNING = CONF['overlay']['colors']['warning']
    OVERLAY_COLOR_ERROR = CONF['overlay']['colors']['error']
    OVERLAY_COLOR_JEGG = CONF['overlay']['colors']['jegg']

    LOG.info('Overlay configuration loaded successfully.')

except Exception:
    LOG.exception('An error has occured while reading the OVERLAY section of the config: ')
    sys.exit(1)

print('\n')