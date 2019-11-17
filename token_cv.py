import json
import pytesseract
import cv2

from imagesearch import *


# provided an image, determine if we are looking at a loot screen
# and return the answer
def detect_loot_screen(screen_grab, slice, target):

    # slice off the critical area from full-screen capture
    # (ie. the area that contains loot screen header)
    image_slice = np.array(screen_grab)[slice[0]:slice[1], slice[2]:slice[3], :]

    # attempt to detect the header
    detect = imagesearcharea(target, 0, 0, 0, 0, precision=0.8, im=image_slice)

    # if header found at any position, return true
    if detect[0] != -1:
        return True
    else:
        return False


# provided an image, determine if we had a token drop in loot screen
# and return the answer
def detect_token_drop(screen_grab, slice, target):

    # slice off the critical area from full-screen capture 
    # (ie. the area that contains loot drops)
    image_slice = np.array(screen_grab)[slice[0]:slice[1], slice[2]:slice[3], :]

    # attempt to detect the token
    detect =  imagesearcharea(target, 0, 0, 0, 0, precision=0.9, im=image_slice)

    # if token found at any position, return true
    if detect[0] != -1:
        return True
    else:
        return False


# a function to determine the hunt type from image
# using OCR on behemoth name
def read_hunt_type(screen_grab, slice, tess_config=None):

    # slice off the critical area from full-screen capture 
    # (ie. the area that contains behemoth name)
    image_slice = np.array(screen_grab)[slice[0]:slice[1], slice[2]:slice[3], :]

    # thresholding to increase tesseract's ability to read the image
    ret, ocr_image = cv2.threshold(image_slice, 100, 255, cv2.THRESH_BINARY_INV)


    # read the name; config supplied with the project is recommended
    # as it disables dictionary search; Behemoth names are not found in dictionaries
    name = pytesseract.image_to_string(ocr_image, config=tess_config)


    # utilise hunt dictionary to transform behemoth name into a hunt category
    with open('./data/json/hunts.json', 'r') as json_file:
        hunt_dict = json.load(json_file)


    # return None if unable to determine valid hunt category
    if name in hunt_dict.keys():
        return hunt_dict[name]
    else:
        return None