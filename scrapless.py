import json
import time
import datetime
import pytesseract
import cv2
import logging

from imagesearch import *
from token_cv import *
from helpers import *
from forms import *


# read paremetres from JSON
with open('./data/json/config.json', 'r') as config_file:
    config = json.load(config_file)

# configure log file
log = get_logger()

# configure tesseract path
pytesseract.pytesseract.tesseract_cmd = config['tesseract_path']


# generate random user string if no name is provided
if config['user'] == '':

    log.info('No user found, generating random ID')

    config['user'] = id_generator()
    
    # save updated config
    with open('./data/json/config.json', 'w') as dump_file:
        json.dump(config, dump_file, indent=2, separators=(',',':'))


# read the screen size and screen region capture from config
screen_region = tuple([config[x] for x in ['screen_x','screen_y','screen_width','screen_height']])
scn_wdth = config['screen_width']
scn_hght = config['screen_height']


# data for processing the loot screen
loot_data = {
    'loot_slice': [config[x] for x in ['loot_height_start','loot_height_end','loot_width_start','loot_width_end']],
    'loot_img': f'./data/images/targets/loot_screen/{scn_wdth}_{scn_hght}_loot.png',

    'token_slice': [config[x] for x in ['token_height_start','token_height_end','token_width_start','token_width_end']],
    'token_img': f'./data/images/targets/token/{scn_wdth}_{scn_hght}_token.png',

    'behe_slice': [config[x] for x in ['behe_height_start','behe_height_end','behe_width_start','behe_width_end']],
}


# data for processing the lobby screen
lobby_data = {
    'lobby_slice': [config[x] for x in ['lobby_height_start','lobby_height_end','lobby_width_start','lobby_width_end']],
    'lobby_img': f'./data/images/targets/lobby_screen/{scn_wdth}_{scn_hght}_lobby.png',

    'patrol_slice': [config[x] for x in ['patrol_height_start','patrol_height_end','patrol_width_start','patrol_width_end']],
    'patrol_img': f'./data/images/targets/patrol_screen/{scn_wdth}_{scn_hght}_patrol.png',

    'threat_slice': [config[x] for x in ['threat_height_start','threat_height_end','threat_width_start','threat_width_end']],
}


# store threat level
threat_level = -1
hunt_type = ''


# work in the loop of image recognition
while True:

    try:

        # pause between captures
        time.sleep(1)

        # capture the current state of the screen
        screen_grab = region_grabber(screen_region)


        # process lobby visual data
        threat_level, hunt_type = lobby_reader(screen_grab, lobby_data, threat_level, hunt_type, log)


        # don't bother further if threat is too low
        if threat_level > -1:

            # process loot screen visual data
            threat_level = loot_reader(screen_grab, loot_data, threat_level, hunt_type, config, log)
    

    except Exception:

        log.exception('An exception has occured:')