import traceback
import inspect
import string
import logging

from datetime import datetime
from imagesearch import *
from token_cv import *
from forms import *

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


'''
Helper function which wraps all the lobby image detection and OCR under one name, 
to clean up the main file code a little
'''
def lobby_reader(screen_grab, lobby_data, log):

    lobby_slice = lobby_data['lobby_slice']
    lobby_img = lobby_data['lobby_img']

    patrol_slice = lobby_data['patrol_slice']
    patrol_img = lobby_data['patrol_img']

    threat_slice = lobby_data['threat_slice']

    threat_level = -1
    hunt_type = ''


    # determine the hunt only if we see the lobby
    if detect_element(screen_grab, lobby_slice, lobby_img):

        threat_level = read_threat_level(screen_grab, threat_slice)
        hunt_type = 'Patrol' if detect_element(screen_grab, patrol_slice, patrol_img) else 'Pursuit'
        
        # open log file
        log.info(f'Lobby detected, threat level {threat_level} {hunt_type}')

        # take a break to save resources
        time.sleep(30)

    return threat_level, hunt_type


'''
Helper function which wraps all the loot image detection and OCR under one name,
to clean up the main file code a little
'''
def loot_reader(screen_grab, loot_data, threat_level, hunt_type, config, log):

    loot_slice = loot_data['loot_slice']
    loot_img = loot_data['loot_img']

    token_slice = loot_data['token_slice']
    token_img = loot_data['token_img']

    behe_slice = loot_data['behe_slice']

    # proceed further only if loot screen is detected
    if detect_element(screen_grab, loot_slice, loot_img, prec=0.7):

        # determine if we had a token drop
        if_drop = 'Yes' if detect_element(screen_grab, token_slice, token_img, prec=0.95) else 'No'

        # determine behemoth name
        behemoth_name = read_behemoth(screen_grab, slice=behe_slice, tess_config=config['tesseract_conf'])
        behemoth_name = trim_behemoth_name(behemoth_name)

        # determine hunt category
        hunt_tier = get_hunt_tier(threat_level)

        # read patch version
        patch_ver = get_patch_version(config['game_path'])
        
        # read user
        user = config['user']

        # send data to Forms
        fill_basic_form(if_drop, hunt_cat, patch_ver)
        fill_rich_form(if_drop, hunt_type, hunt_tier, threat_level, behemoth_name, patch_ver, user)

        # open log file
        log.info(f'Submitted form: {if_drop} - {hunt_tier} - {patch_ver}')
        log.info(f'Submitted form: {if_drop} - {hunt_type} - {hunt_tier} - {threat_level} - {behemoth_name} - {patch_ver} - {user}')

        # reset threat level
        threat_level = -1

    return threat_level


'''
Helper function designed solely to return hunt tier
for a given threat level. Basic logic, simple functionality
Should possibly move the values to global variables
'''
def get_hunt_tier(threat_level):

    if threat_level <= 7:
        return 'Neutral/Elemental'
    elif threat_level <= 12:
        return 'Dire'
    elif threat_level <= 16:
        return 'Heroic'
    elif threat_level <= 22:
        return 'Heroic+'


'''
Helper function for recovering the current patch version the game
is being played on. This is not resistant to people not logging out
of the game for no-downtime patches, but saves a lot of work otherwise.
Requires game installation path to work properly
'''
def get_patch_version(game_path):

    # open version file from the specified path
    with open(f'{game_path}/Version.txt', 'r') as version_file:

        # read the only line in the file
        file_line = version_file.readline()

        # extract patch version
        patch = file_line.split('_')[1].split('-')[1]

        # return the patch
        return patch


'''
Simple function that wraps up all the processing applicable to behemoth name
to reduce it to the basic "species".
'''
def trim_behemoth_name(name):

    name = name.replace(' (Heroic)', '')
    name = name.split(' ')[-1]

    return name


'''
Generates a random ID in the form of string of desired length
This is used in case a user doesn't want to be identified by their 
username in data collection and aggregation process
'''
def id_generator(size=20, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))