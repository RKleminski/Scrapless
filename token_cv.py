import json
import pytesseract
import cv2

from imagesearch import *


# provided an image, determine if an interesting element is in sight
def detect_element(screen_grab, slice, target, prec=0.8):

    # slice off the critical area from full-screen capture
    image_slice = np.array(screen_grab)[slice[0]:slice[1], slice[2]:slice[3], :]

    # attempt to detect the target
    detect = imagesearcharea(target, 0, 0, 0, 0, precision=prec, im=image_slice)

    # if target found at any position, return true
    if detect[0] != -1:
        return True
    else:
        return False


# provided an image of the lobby, retrieve threat level of the hunt queued for
def read_threat_level(screen_grab, slice, tess_config=None):

    # slice off the critical area from full-screen capture 
    # (ie. the area that contains threat level)
    image_slice = np.array(screen_grab)[slice[0]:slice[1], slice[2]:slice[3], :]

    # preprocessing to increase tesseract's ability to read the image
    image_slice = cv2.cvtColor(image_slice, cv2.COLOR_RGB2GRAY)
    image_slice = cv2.resize(image_slice, (520, 470))
    ret, ocr_image = cv2.threshold(image_slice, 250, 255, cv2.THRESH_BINARY)
    ocr_image = cv2.bitwise_not(ocr_image)

    # read the name; config supplied with the project is recommended
    # as it disables dictionary search; Behemoth names are not found in dictionaries
    threat = pytesseract.image_to_string(ocr_image, config='digits')

    # return the threat level
    return int(threat) if threat != '' else 0


# a function to determine the hunted behemoth
def read_behemoth(screen_grab, slice, tess_config=None):

    # slice off the critical area from full-screen capture 
    # (ie. the area that contains behemoth name)
    image_slice = np.array(screen_grab)[slice[0]:slice[1], slice[2]:slice[3], :]

    # thresholding to increase tesseract's ability to read the image
    ret, ocr_image = cv2.threshold(image_slice, 100, 255, cv2.THRESH_BINARY_INV)


    # read the name; config supplied with the project is recommended
    # as it disables dictionary search; Behemoth names are not found in dictionaries
    name = pytesseract.image_to_string(ocr_image, config=tess_config)

    return name