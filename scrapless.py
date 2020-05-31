import time
import pytesseract
import settings as stng
import tkinter
import pyautogui
import sys
import random
import os

from win32 import win32gui
from uuid import uuid4
import win32con

from fuzzywuzzy import fuzz, process

import numpy as np
import cv2
import re

from app import App

'''
Bread and butter of the program, running in a loop to continously
read the screen of the user, in order to recover data and process
data collecting efforts
'''
def blblblblb():
    
    # variable to control the current operations of the program
    program_mode = 'RAMSGATE'

    # dict for storing hunt data
    hunt_data = {}

    # work in the loop of image recognition
    while True:

        # if bounty drafting detected, inform the user and proceed to read the screen
        # ===========================================================================
        if program_mode == 'IN_DRAFT':

            # read bounty reward and translate it to names
            bounty_value = cvt.read_bounty_value(screen_grab, stng.BOUNTY_VAL_SLC)
            bounty_tier = utils.get_bounty_tier(bounty_value)

            if bounty_tier == 'ERROR':

                # increment error counter
                error_count += 1
                
                # inform the user of retrying and loop back if error threshold not reached
                if error_count <= 5:

                    system_message = f'WARNING: Invalid bounty value of {bounty_value} detected. Retrying...'
                    overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_WARNING, overlay_labels)
                
                elif error_count > 5:

                    system_message = 'ERROR: Retry limit reached. Data will not be submitted.\n'
                    overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_ERROR, overlay_labels)
                    program_mode = 'RAMSGATE'

            else:

                system_message = f'{bounty_tier} bounty drafting detected. Awaiting draft end.'
                overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_SUCCESS, overlay_labels)
                program_mode = 'END_DRAFT'


        # if bounty tier detected, wait for the end of drafting
        # ===========================================================================
        elif program_mode == 'END_DRAFT':

            # detect the player returning to bounty menu
            if cvt.detect_element(screen_grab, stng.BOUNTY_MENU_SLC, stng.BOUNTY_MENU_IMG):

                bounty_data = {
                    'rarity': bounty_tier,
                    'patch_ver': stng.GAME_VER,
                    'user': stng.USER
                }

                system_message = f'Submitted data: {" - ".join(bounty_data.values())}.'
                overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_SUCCESS, overlay_labels)
                program_mode = 'RAMSGATE'
                
                # submit data
                forms.bounty_form_submit(bounty_data)


        # if trial lobby detected, wait for loot to display a message
        # ===========================================================================
        elif program_mode == 'IN_TRIAL':

            # if loot screen detected
            if cvt.detect_element(screen_grab, stng.TRIAL_RES_SLC, stng.TRIAL_RES_IMG):
                

                # read behemoth name on loot screen
                behemoth_name = cvt.read_behemoth(screen_grab, stng.BHMT_TRIAL_SLC, inverse=True, tess_config=stng.TESS_CONF)
                behemoth_name = utils.trim_behemoth_name(behemoth_name)

                # print a line depending on victory or defeat
                if behemoth_name == 'Defeated':

                    system_message = utils.trial_defeat_line(threat_level)
                    overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_JEGG, overlay_labels)

                else:

                    system_message = utils.trial_victory_line(threat_level)
                    overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_JEGG, overlay_labels)

                # return to normal operation of the program
                program_mode = 'RAMSGATE'


        # await loot screen if currently in a regular hunt
        # ===========================================================================
        elif program_mode == 'IN_HUNT':

            # if loot screen detected, set program to read loot
            if cvt.detect_element(screen_grab, stng.LOOT_SLC, stng.LOOT_IMG, prec=0.8):
                
                system_message = f'Loot screen detected, processing...'
                overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_INFO, overlay_labels)
                program_mode = 'IN_LOOT'


        # read loot data if in loot screen
        # ===========================================================================
        elif program_mode == 'IN_LOOT':

            # read loot data
            loot_status, loot_data = loot_screen_reader(screen_grab, hunt_data, overlay_labels)

            # accept defeat and reset program mode
            if loot_status == 'DEFEAT':

                system_message = 'DEFEAT: The party has been defeated, no data will be submitted.\n'
                overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_WARNING, overlay_labels)
                hunt_data = {}
                program_mode = 'RAMSGATE'


            # otherwise, if everything is fine, submit data
            elif loot_status == 'OK':

                for data in loot_data:
                    forms.loot_drop_submit(data)

                system_message = f'Loot data submitted.\n'
                overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_SUCCESS, overlay_labels)
                hunt_data = {}
                program_mode = 'RAMSGATE'


            # otherwise, if error occured, retry
            elif loot_status == 'ERROR':

                # if suspicious loot numbers are present, save screenshot for future reference
                if loot_data ==  'TOO_MANY_DROPS':
                    system_message = f'ERROR: Suspiciously big stack of loot. Screenshot saved, data won\'t be submitted.'
                    overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_ERROR, overlay_labels)

                    # prepare a path for saving the error-causing
                    path = './error_imgs/'
                    if not os.path.exists(path):
                        os.makedirs(path)
                    
                    # transform error image grab for saving
                    err_grab = np.array(screen_grab)
                    err_grab = cv2.cvtColor(err_grab, cv2.COLOR_RGB2BGR)

                    # save error grab to disk
                    cv2.imwrite(f'{path}{uuid4()}.png', err_grab)

                    program_mode = 'RAMSGATE'

                # otherwise handle the error normally
                else:
                    # increment error counter
                    error_count += 1
                    
                    # inform the user of retrying and loop back if error threshold not reached
                    if error_count <= 5:

                        system_message = f'WARNING: Expected behemoth {loot_data["lobby_behemoth"]} but found {loot_data["loot_behemoth"]}. Retrying...'
                        overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_WARNING, overlay_labels)

                        # prepare a path for saving the error-causing
                        path = './error_imgs/'
                        if not os.path.exists(path):
                            os.makedirs(path)
                        
                        # transform error image grab for saving
                        err_grab = np.array(screen_grab)
                        err_grab = cv2.cvtColor(err_grab, cv2.COLOR_RGB2BGR)

                        # save error grab to disk
                        cv2.imwrite(f'{path}{uuid4()}.png', err_grab)
                        
                        program_mode = 'IN_LOOT'
                        time.sleep(error_count)

                    elif error_count > 5:

                        system_message = 'ERROR: Retry limit reached. Data will not be submitted.\n'
                        overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_ERROR, overlay_labels)

                        hunt_data = {}
                        program_mode = 'RAMSGATE'


def main():

    # new instance of the main class
    scrapless = App()

    # operate in an infinite loop
    while True:

        # capture the screen
        scrapless.screenCap()

        scrapless.processScreen()

        # refresh the overlay to keep it responsive, if present
        if scrapless.overlay.enabled:
            scrapless.overlay.refresh()

        # throttle the loop for performance
        time.sleep(0.2)


'''
Standard stuff, run main function if running the file
'''
if __name__ == '__main__':
    main()