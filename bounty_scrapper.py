import json
import time
import datetime
import pytesseract
import cv2

from imagesearch import *
from token_cv import *
from helpers import *


# read paremetres from JSON
with open('./data/json/config.json', 'r') as config_file:
    config = json.load(config_file)


# configure tesseract path
pytesseract.pytesseract.tesseract_cmd = config['tesseract_path']

# read the screen size and screen region capture from config
screen_region = tuple([config[x] for x in ['screen_x','screen_y','screen_width', 'screen_height']])
scn_wdth = config['screen_width']
scn_hght = config['screen_height']


# read the lobby capture slice coordinates from config 
lobby_slice = [config[x] for x in ['lobby_height_start','lobby_height_end','lobby_width_start','lobby_width_end']]

# read the threat capture slice coordinates from config
threat_slice = [config[x] for x in ['threat_height_start','threat_height_end','threat_width_start','threat_width_end']]

# read the patrol capture slice coordinates from config
patrol_slice = [config[x] for x in ['patrol_height_start','patrol_height_end','patrol_width_start','patrol_width_end']]

# read the loot capture slice coordinates from config 
loot_slice = [config[x] for x in ['loot_height_start','loot_height_end','loot_width_start','loot_width_end']]

# read the behemoth capture slice coordinates from config
behe_slice = [config[x] for x in ['behe_height_start','behe_height_end','behe_width_start','behe_width_end']]

# read the token capture slice coordinates from config 
token_slice = [config[x] for x in ['token_height_start','token_height_end','token_width_start','token_width_end']]

# construct paths for recognition images
token_img = f'./data/images/targets/token/{scn_wdth}_{scn_hght}_token.png'
loot_img = f'./data/images/targets/loot_screen/{scn_wdth}_{scn_hght}_loot.png'
lobby_img = f'./data/images/targets/lobby_screen/{scn_wdth}_{scn_hght}_lobby.png'
patrol_img = f'./data/images/targets/patrol_screen/{scn_wdth}_{scn_hght}_patrol.png'

# store threat level
threat_level = 0
hunt_type = ''

# work in the loop of image recognition
while True:

    # pause for a second between captures
    # to save system resources
    time.sleep(1)


    # capture the current state of the screen
    screen_grab = region_grabber(screen_region)


    # determine the hunt only if we see the lobby
    if detect_element(screen_grab, lobby_slice, lobby_img):

        threat_level = read_threat_level(screen_grab, threat_slice, tess_config=config['tesseract_conf'])
        hunt_type = 'Patrol' if detect_element(screen_grab, patrol_slice, patrol_img) else 'Pursuit'
        print(f'We are in a lobby, threat level {threat_level} {hunt_type}')


    # don't bother further if threat is too low
    if threat_level >= 2:

        # proceed further only if loot screen is detected
        if detect_element(screen_grab, loot_slice, loot_img):

            # determine if we had a token drop
            if_drop = 'Yes' if detect_element(screen_grab, token_slice, token_img, prec=0.95) else 'No'

            # determine behemoth name
            behemoth_name = read_behemoth(screen_grab, slice=behe_slice, tess_config=config['tesseract_conf']).replace(" ","_")

            # determine hunt category
            hunt_cat = hunt_category(threat_level)

            # save screen_grab for hand evaluation
            print(f'./test_grabs/{if_drop}_{behemoth_name}_T{str(threat_level)}_{hunt_cat}_{hunt_type}_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.png')
            cv2.imwrite(f'./test_grabs/{if_drop}_{behemoth_name}_T{str(threat_level)}_{hunt_cat}_{hunt_type}_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.png', np.array(screen_grab))
            
            # wait two minutes to ensure no duplicate loot drops are recorded
            time.sleep(120)