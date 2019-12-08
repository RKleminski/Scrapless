import json
import pytesseract
import cv2
import numpy as np
import pyautogui


'''
Returns a designated area of the screen
'''
def region_grabber(region):
    
    x1 = region[0]
    y1 = region[1]
    width = region[2] - x1
    height = region[3] - y1

    return pyautogui.screenshot(region=(x1, y1, width, height))


'''
Function for detecting a template element on the provided image
Requires a screen grab, slice coordinates, target template and precision
Precision can be tweaked for detection of animated elements and similar
Slice is not necessary, but allows for highly targeted search to minimise 
false positives
'''
def detect_element(screen_grab, slice, target, prec=0.8):

    # slice off the critical area from full-screen capture
    image_slice = np.array(screen_grab)[slice[0]:slice[1], slice[2]:slice[3], :]
    image_slice = cv2.cvtColor(image_slice, cv2.COLOR_RGB2GRAY)

    cv2.imwrite('./test_detect.png', image_slice)
    cv2.imwrite('./test_target.png', target)

    res = cv2.matchTemplate(image_slice, target, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    
    # if target found at any position, return true
    if max_val < prec:
        return False
    return True


'''
Looks into the specified slice of the screen grab for a number expressing threat level
of the hunt for which the player is in the lobby for

The config supplied disables segmenting and looks for digits only
this is necessary to correctly read the threat level
'''
def read_threat_level(screen_grab, slice):

    # slice off the critical area from full-screen capture 
    image_slice = np.array(screen_grab)[slice[0]:slice[1], slice[2]:slice[3], :]

    # preprocessing to increase tesseract's ability to read the image
    # most important here is the upscaling, followed by binarisation and inversion
    image_slice = cv2.cvtColor(image_slice, cv2.COLOR_RGB2GRAY)
    
    width = int(image_slice.shape[1] * 10)
    height = int(image_slice.shape[0] * 10)
    dim = (width, height)

    image_slice = cv2.resize(image_slice, dim, interpolation=cv2.INTER_AREA)
    
    ret, ocr_image = cv2.threshold(image_slice, 254, 255, cv2.THRESH_BINARY)
    ocr_image = cv2.bitwise_not(ocr_image)
    
    cv2.imwrite('./test_ocr.png', ocr_image)

    # read the threat level
    threat = pytesseract.image_to_string(ocr_image, lang='eng', config='--psm 13 digits')

    # return the threat level
    return threat if threat != '' else 0


'''
Looks into the specified slice of the screen grab for a numeric record of hunt's completion time.
'''
def read_hunt_time(screen_grab, slice):

    # slice off the critical area from full-screen capture
    image_slice = np.array(screen_grab)[slice[0]:slice[1], slice[2]:slice[3], :]

    # preprocessing to increase tesseract's ability to read the image
    # most important here is the upscaling, followed by binarisation and inversion
    image_slice = cv2.cvtColor(image_slice, cv2.COLOR_RGB2GRAY)
    image_slice = cv2.resize(image_slice, (520, 470))
    ret, ocr_image = cv2.threshold(image_slice, 250, 255, cv2.THRESH_BINARY)
    ocr_image = cv2.bitwise_not(ocr_image)
    
    # read the hunt time
    time = pytesseract.image_to_string(ocr_image, lang='eng', config='--psm 13 digits')

    return time if time != '' else 0


'''
Similar to the function for reading the threat level, this one retrieves the full name of
the behemoth. This allows for some more fine-grained data gathering

Config supplied with the project is recommended, as it disables dictionary search;
behemoth names are not real english words, so the dictionaries get needlessly confused
when trying to determine them as a word

Inverse parameter dictates whether a binary NOT should be applied to the entire image
This is necessary to properly read behemoth names in lobby, but will throw your results 
off in the loot screen
'''
def read_behemoth(screen_grab, slice, inverse=False, tess_config=None):

    # slice off the critical area from full-screen capture 
    image_slice = np.array(screen_grab)[slice[0]:slice[1], slice[2]:slice[3], :]

    # thresholding to increase tesseract's ability to read the image
    ret, ocr_image = cv2.threshold(image_slice, 100, 255, cv2.THRESH_BINARY_INV)

    if inverse:
        ocr_image = cv2.bitwise_not(ocr_image)

    # read the behemoth name
    name = pytesseract.image_to_string(ocr_image, config=tess_config)

    return name