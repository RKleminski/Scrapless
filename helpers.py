import traceback
import inspect

from datetime import datetime
from imagesearch import *
from token_cv import *
from forms import *

'''
Helper function which essentially just wraps all the lobby
image detection and OCR under one name, to clean up the main
file code a little
'''
def lobby_reader(screen_grab, lobby_data):

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
        with open('./scrapless.log', 'w') as log_file:
            log_file.write(f'Lobby detected, threat level {threat_level} {hunt_type} \n')
        print(f'Lobby detected, threat level {threat_level} {hunt_type}')

        # save an image along with what number was read in the name
        cv2.imwrite(f'./ocr_grabs/{threat_level}_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.png', np.array(screen_grab))

    return threat_level, hunt_type


'''
'''
def loot_reader(screen_grab, loot_data, threat_level, hunt_type, config):

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
        behemoth_name = read_behemoth(screen_grab, slice=behe_slice, tess_config=config['tesseract_conf']).replace(" ","_")

        # determine hunt category
        hunt_cat = hunt_category(threat_level)
        hunt_cat = hunt_cat # temporary line for while we are testing on windows

        # read patch version
        patch_ver = get_patch_version(config['game_path'])

        # save screen_grab for hand evaluation
        cv2.imwrite(f'./test_grabs/{if_drop}_{behemoth_name}_T{str(threat_level)}_{hunt_cat.replace("/", "-")}_{hunt_type}_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.png', np.array(screen_grab))
        
        # open log file
        with open('./scrapless.log', 'w') as log_file:
            log_file.write(f'./test_grabs/{if_drop}_{behemoth_name}_T{str(threat_level)}_{hunt_cat}_{hunt_type}_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.png')
        print(f'./test_grabs/{if_drop}_{behemoth_name}_T{str(threat_level)}_{hunt_cat}_{hunt_type}_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.png')
        
        # send data to Forms
        fill_basic_form(if_drop, hunt_cat, patch_ver)

        # open log file
        with open('./scrapless.log', 'w') as log_file:
            log_file.write(f'Submitted form: {if_drop} - {hunt_cat} - {patch_ver}\n')
        print(f'Submitted form: {if_drop} - {hunt_cat} - {patch_ver}')

        # reset threat level
        threat_level = -1

    return threat_level


'''
Helper function designed solely to return hunt category
for a given threat level. Basic logic, simple functionality
Should possibly move the values to global variables
'''
def hunt_category(threat_level):

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
    with open(f'{game_path}\\Version.txt', 'r') as version_file:

        # read the only line in the file
        file_line = version_file.readline()

        # extract patch version
        patch = file_line.split('_')[1].split('-')[1]

        # return the patch
        return patch


'''
Provided an exception, the function will save traceback as a unique log file
for easier managing of exceptions
'''
def exception_handler(Exception, fun_name=''):
    
    # get function name if not specified
    if fun_name == '':
        fun_name = inspect.stack()[1][3]

        if fun_name == '<module>':
            fun_name = 'scrapless'


    # log the error to a text file
    with open(f'./error_logs/{datetime.now().strftime("%Y-%m-%d_%H:%M:%S").replace(":","-")}_{fun_name}.log', 'w') as err_file:
        traceback.print_exc(10000, err_file)