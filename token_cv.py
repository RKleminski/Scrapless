import json
import pytesseract
import cv2
import numpy as np
import pyautogui


'''
Looks into the specified slice of the screen grab for a numeric record of hunt's completion time.
'''
def read_hunt_time(screen_grab, slice):

    # slice off the critical area from full-screen capture
    image_slice = np.array(screen_grab)[slice[0]:slice[1], slice[2]:slice[3], :]

    # preprocessing to increase tesseract's ability to read the image
    # most important here is the upscaling, followed by binarisation and inversion
    image_slice = cv2.cvtColor(image_slice, cv2.COLOR_RGB2GRAY)

    # invert the colours
    image_slice = cv2.bitwise_not(image_slice)

    # threshold
    ret, ocr_image = cv2.threshold(image_slice, 150, 255, cv2.THRESH_BINARY)

    # determine resize dimensions
    width = int(ocr_image.shape[1] * 14)
    height = int(ocr_image.shape[0] * 15)
    dim = (width, height)

    # resize
    ocr_image = cv2.resize(ocr_image, dim, interpolation=cv2.INTER_AREA)

    # read the hunt time
    time = pytesseract.image_to_string(ocr_image, lang='eng', config='--psm 13 -c tessedit_char_whitelist=0123456789:.')

    return time if time != '' else 0

def read_death_count(screen_grab, slice):

        # slice off the critical area from full-screen capture
    image_slice = np.array(screen_grab)[slice[0]:slice[1], slice[2]:slice[3], :]

    # preprocessing to increase tesseract's ability to read the image
    # most important here is the upscaling, followed by binarisation and inversion
    image_slice = cv2.cvtColor(image_slice, cv2.COLOR_RGB2GRAY)

    # invert the colours
    image_slice = cv2.bitwise_not(image_slice)

    # threshold
    ret, ocr_image = cv2.threshold(image_slice, 150, 255, cv2.THRESH_BINARY)

    # determine resize dimensions
    width = int(ocr_image.shape[1] * 15)
    height = int(ocr_image.shape[0] * 15)
    dim = (width, height)

    # resize
    ocr_image = cv2.resize(ocr_image, dim, interpolation=cv2.INTER_AREA)

    # read the hunt time
    death_text = pytesseract.image_to_string(ocr_image, lang='eng', config='--psm 13').lower()

    if 'never' in death_text:
        return 0
    elif 'once' in death_text:
        return 1
    elif 'twice' in death_text:
        return 2
    else:
        return 3

def read_loot_section(screen_grab, slice):

    # slice off the critical area from full-screen capture 
    image_slice = np.array(screen_grab)[slice[0]:slice[1], slice[2]:slice[3], :]

    # convert to grayscale
    image_slice = cv2.cvtColor(image_slice, cv2.COLOR_RGB2GRAY)

    # determine resize dimensions
    width = int(image_slice.shape[1] * 15)
    height = int(image_slice.shape[0] * 15)
    dim = (width, height)

    # resize
    image_slice = cv2.resize(image_slice, dim, interpolation=cv2.INTER_AREA)

    # thresholding to increase tesseract's ability to read the image
    image_slice = cv2.bitwise_not(image_slice)
    ret, ocr_image = cv2.threshold(image_slice, 125, 255, cv2.THRESH_BINARY)

    # read the behemoth name
    return(pytesseract.image_to_string(ocr_image, config='--psm 11'))


def read_bounty_value(screen_grab, slice):

    # slice off the critical area from full-screen capture 
    image_slice = np.array(screen_grab)[slice[0]:slice[1], slice[2]:slice[3], :]

    # preprocessing to increase tesseract's ability to read the image
    # most important here is the upscaling, followed by binarisation and inversion
    image_slice = cv2.cvtColor(image_slice, cv2.COLOR_RGB2GRAY)
    
    width = int(image_slice.shape[1] * 5)
    height = int(image_slice.shape[0] * 5)
    dim = (width, height)

    image_slice = cv2.resize(image_slice, dim, interpolation=cv2.INTER_AREA)
    
    ret, ocr_image = cv2.threshold(image_slice, 175, 255, cv2.THRESH_BINARY)
    ocr_image = cv2.bitwise_not(ocr_image)

    # read bounty value
    return pytesseract.image_to_string(ocr_image, config='--psm 13 -c tessedit_char_whitelist=x0123456789')