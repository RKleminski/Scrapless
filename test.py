import json
import time
import pytesseract
import cv2
from imagesearch import *


# read paremetres from JSON
with open('./config.json', 'r') as config_file:
    config = json.load(config_file)

#  configure tesseract path
pytesseract.pytesseract.tesseract_cmd = config['tesseract_path']

# read the screen size 
scn_wdth = config['screen_width']
scn_hght = config['screen_height']


# read the loot capture size 
cap_wdth = config['capture_width']
cap_hght = config['capture_height']


# read the hunt capture size 
hnt_wdth = config['hunt_width']
hnt_hght = config['hunt_height']


# construct paths for recognition images
token_img = f'./target_images/token/{scn_wdth}_{scn_hght}_token.png'
loot_img = f'./target_images/loot_screen/{scn_wdth}_{scn_hght}_loot.png'




# work in the loop of image recognition
while True:

    # pause for a second between captures
    # to save system resources
    time.sleep(1)

    scrn = region_grabber((0, 0, scn_wdth, scn_hght))

    hunt_name_im = np.array(scrn)[20:50, 95:395, :]
    ret, hunt_name_im = cv2.threshold(hunt_name_im, 100, 255, cv2.THRESH_BINARY_INV)
    print(pytesseract.image_to_string(hunt_name_im, config='./dauntless'))

#     # screen-grab relevant part of the screen to use for both comparisons
#     im = region_grabber((0, 0, cap_wdth, cap_hght))

#     # check if we are looking at the loot scren
#     res = imagesearcharea(loot_img, 0, 0, cap_wdth, cap_hght, 0.8, im)

#     # if we are, proceed further
#     if res[0] != -1:

#         print('Loot screen recognised')

#         # check if we see the loot token drop
#         res = imagesearcharea(token_img, 0, 0, cap_wdth, cap_hght, 0.95, im)

#         # if we are, note that down
#         if res[0] != -1:

#             # NOTE: after seeing a token drop, a cooldown of two minutes should be engaged to prevent duplicate submission
#             print('Token drop found')
#             print(res)