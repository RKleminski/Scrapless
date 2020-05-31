import json
import pytesseract
import cv2
import numpy as np
import pyautogui

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