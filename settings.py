import json
import random
import string
import logging
import cv2

from datetime import datetime

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


# ======
#
LOG = get_logger()


# ======
#
print('=============================')
print('=== WELCOME TO SCRAPLESS! ===')
print('=============================')
print('\n')


# ======
#
CONF_PTH = './data/json/config.json'

with open(CONF_PTH, 'r') as conf_file:
    CONF = json.load(conf_file)

LOG.info('SETUP: Config file read successfully.')


# ======
#
HUNT_PTH = './data/json/hunts.json'

# read file of allowed hunts
with open(HUNT_PTH, 'r') as hunt_file:
    HUNT = json.load(hunt_file)

LOG.info('SETUP: Valid hunt references loaded.')


# ======
#
GAME_PTH = CONF['paths']['game']
TESS_PTH = CONF['paths']['tesseract']
TESS_CONF = CONF['paths']['tesseract_conf']

LOG.info('SETUP: Game and Tesseract paths loaded.')


# ======
#
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

LOG.info(f'SETUP: Screen specifications found, {SCRN_WDT}x{SCRN_HGT}p resolution, {A_RATIO} aspect ratio.')


'''
Function to initalise random user ID if the person running the program
decides to remain anonymous
'''
def user_init():

    global CONF

    LOG.info('SETUP: No username found, generating a random user ID.')

    chars = string.ascii_uppercase + string.digits
    anon_id = ''.join(random.choice(chars) for _ in range(20))

    CONF['user']['name'] = anon_id

    # save updated config
    with open(CONF_PTH, 'w') as dump_file:
        json.dump(CONF, dump_file, indent=2, separators=(',',':'))

    return anon_id


# ======
#
USER = CONF['user']['name'] if CONF['user']['name'] != "" else user_init()
LOG.info(f'SETUP: Username set to {USER}')


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


# ======
#
GAME_VER = get_patch_version()
LOG.info(f'SETUP: Game version {GAME_VER} detected.')


# ======
#
ASP_CONF_PTH = f'./data/json/{A_RATIO.replace(":","_")}_config.json'

with open(ASP_CONF_PTH, 'r') as conf_file:
    ASP_CONF = json.load(conf_file)

LOG.info(f'SETUP: Config file for {A_RATIO} ratio accessed successfully.')


# ======
#
A_RATIO_PATH = A_RATIO.replace(':','_')

BHMT_LOBBY_SLC = [int(ASP_CONF['lobby']['behemoth_slice']['height_start'] * Y_SCALE),
                  int(ASP_CONF['lobby']['behemoth_slice']['height_end'] * Y_SCALE),
                  int(ASP_CONF['lobby']['behemoth_slice']['width_start'] * X_SCALE),
                  int(ASP_CONF['lobby']['behemoth_slice']['width_end'] * X_SCALE)]

BHMT_LOOT_SLC = [int(ASP_CONF['loot']['behemoth_slice']['height_start'] * Y_SCALE),
                 int(ASP_CONF['loot']['behemoth_slice']['height_end'] * Y_SCALE),
                 int(ASP_CONF['loot']['behemoth_slice']['width_start'] * X_SCALE),
                 int(ASP_CONF['loot']['behemoth_slice']['width_end'] * X_SCALE)]

ESCAL_LOBBY_SLC = [int(ASP_CONF['escalation']['lobby_slice']['height_start'] * Y_SCALE),
                  int(ASP_CONF['escalation']['lobby_slice']['height_end'] * Y_SCALE),
                  int(ASP_CONF['escalation']['lobby_slice']['width_start'] * X_SCALE),
                  int(ASP_CONF['escalation']['lobby_slice']['width_end'] * X_SCALE)]

ESCAL_RANK_SLC = [int(ASP_CONF['escalation']['rank_slice']['height_start'] * Y_SCALE),
                  int(ASP_CONF['escalation']['rank_slice']['height_end'] * Y_SCALE),
                  int(ASP_CONF['escalation']['rank_slice']['width_start'] * X_SCALE),
                  int(ASP_CONF['escalation']['rank_slice']['width_end'] * X_SCALE)]

ESCAL_SUMM_SLC = [int(ASP_CONF['escalation']['summary_slice']['height_start'] * Y_SCALE),
                  int(ASP_CONF['escalation']['summary_slice']['height_end'] * Y_SCALE),
                  int(ASP_CONF['escalation']['summary_slice']['width_start'] * X_SCALE),
                  int(ASP_CONF['escalation']['summary_slice']['width_end'] * X_SCALE)]


ESCAL_SUMM_IMG = cv2.imread(f'./data/images/targets/esc_summary/{A_RATIO_PATH}_esc_summary.png', 0)
new_size = ( int(ESCAL_SUMM_IMG.shape[1] * X_SCALE),  int(ESCAL_SUMM_IMG.shape[0] * Y_SCALE))
ESCAL_SUMM_IMG = cv2.resize(ESCAL_SUMM_IMG, new_size)


LOBBY_SLC = [int(ASP_CONF['lobby']['slice']['height_start'] * Y_SCALE),
             int(ASP_CONF['lobby']['slice']['height_end'] * Y_SCALE),
             int(ASP_CONF['lobby']['slice']['width_start'] * X_SCALE),
             int(ASP_CONF['lobby']['slice']['width_end'] * X_SCALE)]


LOBBY_IMG = cv2.imread(f'./data/images/targets/lobby_screen/{A_RATIO_PATH}_lobby.png', 0)
new_size = ( int(LOBBY_IMG.shape[1] * X_SCALE),  int(LOBBY_IMG.shape[0] * Y_SCALE))
LOBBY_IMG = cv2.resize(LOBBY_IMG, new_size)


LOOT_SLC = [int(ASP_CONF['loot']['slice']['height_start'] * Y_SCALE),
            int(ASP_CONF['loot']['slice']['height_end'] * Y_SCALE),
            int(ASP_CONF['loot']['slice']['width_start'] * X_SCALE),
            int(ASP_CONF['loot']['slice']['width_end'] * X_SCALE)]


LOOT_IMG =  cv2.imread(f'./data/images/targets/loot_screen/{A_RATIO_PATH}_loot.png', 0)
new_size = ( int(LOOT_IMG.shape[1] * X_SCALE),  int(LOOT_IMG.shape[0] * Y_SCALE))
LOOT_IMG = cv2.resize(LOOT_IMG, new_size)


HTYPE_SLC = [int(ASP_CONF['lobby']['hunt_type_slice']['height_start'] * Y_SCALE),
             int(ASP_CONF['lobby']['hunt_type_slice']['height_end'] * Y_SCALE),
             int(ASP_CONF['lobby']['hunt_type_slice']['width_start'] * X_SCALE),
             int(ASP_CONF['lobby']['hunt_type_slice']['width_end'] * X_SCALE)]

HTYPE_IMG = cv2.imread(f'./data/images/targets/patrol_screen/{A_RATIO_PATH}_patrol.png', 0)
new_size = ( int(HTYPE_IMG.shape[1] * X_SCALE),  int(HTYPE_IMG.shape[0] * Y_SCALE))
HTYPE_IMG = cv2.resize(HTYPE_IMG, new_size)

THRT_SLC = [int(ASP_CONF['lobby']['threat_slice']['height_start'] * Y_SCALE),
            int(ASP_CONF['lobby']['threat_slice']['height_end'] * Y_SCALE),
            int(ASP_CONF['lobby']['threat_slice']['width_start'] * X_SCALE),
            int(ASP_CONF['lobby']['threat_slice']['width_end'] * X_SCALE)]

TIME_SLC = [int(ASP_CONF['loot']['time_slice']['height_start'] * Y_SCALE),
            int(ASP_CONF['loot']['time_slice']['height_end'] * Y_SCALE),
            int(ASP_CONF['loot']['time_slice']['width_start'] * X_SCALE),
            int(ASP_CONF['loot']['time_slice']['width_end'] * X_SCALE)]

TOKEN_SLC = [int(ASP_CONF['loot']['token_slice']['height_start'] * Y_SCALE),
             int(ASP_CONF['loot']['token_slice']['height_end'] * Y_SCALE),
             int(ASP_CONF['loot']['token_slice']['width_start'] * X_SCALE),
             int(ASP_CONF['loot']['token_slice']['width_end'] * X_SCALE)]


TOKEN_IMG = cv2.imread(f'./data/images/targets/token/{A_RATIO_PATH}_token.png', 0)
new_size = ( int(TOKEN_IMG.shape[1] * X_SCALE),  int(TOKEN_IMG.shape[0] * Y_SCALE))
TOKEN_IMG = cv2.resize(TOKEN_IMG, new_size)

LOG.info('SETUP: Region and target data read successfully.\n')

OVERLAY_ON = CONF['overlay']['enable'] == 'Yes'
OVERLAY_X = CONF['overlay']['pos_x']
OVERLAY_Y = CONF['overlay']['pos_y']
OVERLAY_MAX_LINES = int(CONF['overlay']['max_lines'])