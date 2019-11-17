import json
import time
import datetime
import pytesseract
import cv2

from imagesearch import *
from token_cv import *


# read paremetres from JSON
with open('./data/json/config.json', 'r') as config_file:
    config = json.load(config_file)


# configure tesseract path
pytesseract.pytesseract.tesseract_cmd = config['tesseract_path']

# read the screen size and screen region capture from config
screen_region = tuple([config[x] for x in ['screen_x','screen_y','screen_width', 'screen_height']])
scn_wdth = config['screen_width']
scn_hght = config['screen_height']

# read the hunt capture slice coordinates from config
hunt_slice = [config[x] for x in ['hunt_height_start','hunt_height_end','hunt_width_start','hunt_width_end']]

# read the loot capture slice coordinates from config 
loot_slice = [config[x] for x in ['loot_height_start','loot_height_end','loot_width_start','loot_width_end']]

# read the loot capture slice coordinates from config 
token_slice = [config[x] for x in ['token_height_start','token_height_end','token_width_start','token_width_end']]

# construct paths for recognition images
token_img = f'./data/images/targets/token/{scn_wdth}_{scn_hght}_token.png'
loot_img = f'./data/images/targets/loot_screen/{scn_wdth}_{scn_hght}_loot_2.png'


# work in the loop of image recognition
while True:

    # pause for a second between captures
    # to save system resources
    time.sleep(1)


    # capture the current state of the screen
    screen_grab = region_grabber(screen_region)

    # proceed further only if loot screen is detected
    if detect_loot_screen(screen_grab, loot_slice, loot_img):

        # determine if we had a token drop
        drop = 'Yes' if  detect_token_drop(screen_grab, token_slice, token_img) else 'No'

        # determine hunt type
        hunt = read_hunt_type(screen_grab, slice=hunt_slice, tess_config=config['tesseract_conf'])

        # save screen_grab for hand evaluation
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        cv2.imwrite(f'./test_grabs/{drop}_{hunt}_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.png', np.array(screen_grab))
        
        # wait two minutes to ensure no duplicate loot drops are recorded
        time.sleep(120)


