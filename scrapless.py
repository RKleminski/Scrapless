import time
import pytesseract
import settings as stng
import tkinter
import pyautogui
import sys

from win32 import win32gui
import win32con

from fuzzywuzzy import fuzz, process

import token_cv as cvt
import utils
import forms

import numpy as np
import cv2
import re

'''
Detects the lobby and determines the type of a lobby the player is currently in
Additionally returns the name of the "target"
'''
def lobby_detect(screen_grab):

    # determine the hunt only if we see the lobby
    if cvt.detect_element(screen_grab, stng.LOBBY_SLC, stng.LOBBY_IMG, prec=0.7):

        # check if escalation lobby
        escalation_level = cvt.read_escalation_level(screen_grab, stng.ESCAL_LOBBY_SLC)

        if escalation_level != '':
            escalation_level = process.extractOne(escalation_level, stng.ESCAL_TIERS, scorer=fuzz.ratio, score_cutoff=90)

            # return escalation mode and name
            if escalation_level != None:
                return 'ESCAL', escalation_level[0]

        # determine behemoth name if method didn't exit with escalation level
        behemoth_name = cvt.read_behemoth(screen_grab, stng.BHMT_LOBBY_SLC, inverse=True, tess_config=stng.TESS_CONF, trim_size=50, thresh=140)

        # process behemoth name if it is an actual hunt lobby
        behemoth_name = utils.trim_behemoth_name(behemoth_name)
        behemoth_name = fuzzy_behemoth(behemoth_name)

        return 'HUNT', behemoth_name

    return 'NO_LOBBY', ''


'''
Helper function which wraps all the lobby image detection and OCR under one name, 
to clean up the main file code a little
'''
def lobby_reader(screen_grab):

    # read threat level and hunt type
    threat_level = cvt.read_threat_level(screen_grab, stng.THRT_SLC)
    hunt_type = 'Patrol' if cvt.detect_element(screen_grab, stng.HTYPE_SLC, stng.HTYPE_IMG) else 'Pursuit'

    return threat_level, hunt_type


'''
Helper function which wraps all the loot image detection and OCR under one name,
to clean up the main file code a little
'''
def loot_screen_reader(screen_grab, threat_level, hunt_type, behemoth_name, overlay_labels):

    # read the behemoth name on screen
    loot_behemoth_name = cvt.read_behemoth(screen_grab, stng.LOOT_BHMT_SLC, inverse=True, tess_config=stng.TESS_CONF, thresh=100)
    loot_behemoth_name = utils.trim_behemoth_name(loot_behemoth_name)

    # finish early if the party has been defeated 
    if loot_behemoth_name == 'Defeated':
        return 'DEFEAT', {}

    # fuzzy match behemoth name to account for small OCR errors
    loot_behemoth_name = fuzzy_behemoth(loot_behemoth_name)


    # check for expected behemoth name and progress accordingly
    if behemoth_name == loot_behemoth_name or behemoth_name in ['Neutral', 'Blaze', 'Frost', 'Terra', 'Shock', 'Dire', 'Heroic', 'Heroic+']:
        
        system_message = f'Valid screenshot captured, you may leave the current screen.'
        overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_INFO, overlay_labels)

        # determine hunt category
        hunt_tier = utils.get_hunt_tier(threat_level)

        # read hunt time
        hunt_time = cvt.read_hunt_time(screen_grab, stng.LOOT_TIME_SLC)

        loot_data = loot_drops_reader(screen_grab, hunt_type, hunt_tier, threat_level, loot_behemoth_name)

        return 'OK', loot_data
    else:
        return 'ERROR', {'lobby_behemoth': behemoth_name, 'loot_behemoth': loot_behemoth_name}


def loot_drops_reader(screen_grab, hunt_type, hunt_tier, threat_level, behemoth_name):

    loot_data = []

    if 'Escalation' in behemoth_name:
        drop_list = [item for sublist in list(stng.DROP.values()) for item in sublist]
        base_rarity = ['Common', 'Rare', 'Epic', 'Artifact'] * len(stng.DROP)
    else:
        drop_list = stng.DROP[behemoth_name]
        base_rarity = ['Common', 'Rare', 'Epic', 'Artifact']

    # loop through areas of loot screen
    for loot_slice in [ stng.LOOT_BASE_SLC, stng.LOOT_BONS_SLC ]:

        # check if part breaks are there
        if cvt.detect_element(screen_grab, stng.LOOT_BASE_SLC, stng.BREAK_IMG, prec=0.9):
                
                # if so, omit them
                part_coord = cvt.locate_element(screen_grab, stng.LOOT_BASE_SLC, stng.BREAK_IMG, prec=0.9)
                loot_slice[1] = part_coord[1]

        # read all text from the area
        loot_drops = cvt.read_loot_section(screen_grab, loot_slice)

        for line in loot_drops.splitlines():

            loot_row = {
                'hunt_type': hunt_type,
                'hunt_tier': hunt_tier,
                'threat_level': str(threat_level),
                'behemoth_name': behemoth_name,
                'patch_ver': stng.GAME_VER,
                'user': stng.USER
            }

            for drop in drop_list:

                if drop in line:
                    loot_row['drop_count'] = re.sub("[^0-9]", "", line.split(" ")[0])
                    loot_row['drop_name'] = drop
                    loot_row['drop_rarity'] = base_rarity[drop_list.index(drop)]
                    loot_data.append(loot_row)

            if 'Cell' in line:
                loot_row['drop_count'] = re.sub("[^0-9]", "", line.split(" ")[0])
                loot_row['drop_name'] = line.split(" ", 1)[1]
                loot_row['drop_rarity'] = 'Uncommon' if '+1' in line else 'Rare'
                loot_data.append(loot_row)

    return loot_data


'''
When proivided with a behemoth name, returns the closes fuzzy match from the list
of valid behemoth names, or empty string if the best match does not score high enough ratio
similarity to the found name.
'''
def fuzzy_behemoth(behemoth_name):

    if behemoth_name in stng.HUNT.keys():
        return behemoth_name
    else:
        match = process.extractOne(behemoth_name, stng.HUNT.keys(), scorer=fuzz.ratio, score_cutoff=80)
        return '' if match is None else match[0]


'''
Sets up the initial window for Tkinter labels which form the overlay
Ensuring parametres like minimum size, staying on top and transparency
Returns the overlay instance and list of labels to keep track of
'''
def overlay_setup(overlay_labels):

    # draw new overlay
    line = f'SCRAPLESS {stng.scrap_ver}'
    color = stng.OVERLAY_COLOR_INFO
    bg_color= stng.OVERLAY_COLOR_BG

    overlay = tkinter.Label(text=line, font=(stng.OVERLAY_FONT, stng.OVERLAY_FONT_SIZE), fg=color, bg=bg_color)
    overlay_labels.append(overlay)
    overlay.pack()

    # configure the overlay according to our needs
    overlay.master.overrideredirect(True)
    overlay.master.geometry(f"+{stng.OVERLAY_X}+{stng.OVERLAY_Y}")
    overlay.master.minsize(500, 20)
    overlay.master.configure(bg=bg_color)
    overlay.master.lift()
    overlay.master.wm_attributes("-topmost", True)
    overlay.master.wm_attributes("-alpha", stng.OVERLAY_OPACITY)

    # set the window to be functionally transparent aka have mouse clicks pass through
    window = win32gui.FindWindow(None, "tk")
    lExStyle = win32gui.GetWindowLong(window, win32con.GWL_EXSTYLE)
    lExStyle |=  win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
    win32gui.SetWindowLong(window, win32con.GWL_EXSTYLE , lExStyle )

    # update overlay and ensure it stays on top
    overlay.master.update()
    overlay.master.lift()

    return overlay, overlay_labels


'''
Update the overlay by creating a new line of label, with desired text and colour
The oldest stored label will be destroyed if line limit is reached
Returns overlay and list of labels to keep track of
'''
def overlay_update(new_line, line_color, overlay_labels):

    while len(overlay_labels) >= stng.OVERLAY_MAX_LINES:
        overlay_labels[0].destroy()
        overlay_labels.pop(0)

    label = tkinter.Label(text=new_line, font=(stng.OVERLAY_FONT, stng.OVERLAY_FONT_SIZE), fg=line_color, bg=stng.OVERLAY_COLOR_BG)
    overlay_labels.append(label)
    label.pack()

    # update overlay and ensure it stays on top
    label.master.update()
    label.master.lift()

    return overlay_labels


'''
A convenience function which automatically handles system output to console, log file
and the overlay, with specified message and color on the overlay
Returns overlay and list of labels to keep track of
'''
def system_output(message, color, overlay_labels):

    if stng.OVERLAY_ON:

        overlay_labels = overlay_update(message.replace('\n', ''), color, overlay_labels)

    stng.LOG.info(message)

    return overlay_labels


'''
Bread and butter of the program, running in a loop to continously
read the screen of the user, in order to recover data and process
data collecting efforts
'''
def main():
    
    # store overlay variables
    overlay = ''
    overlay_labels = []

    # configure overlay if enabled
    if stng.OVERLAY_ON:
        overlay, overlay_labels = overlay_setup(overlay_labels)

    # configure tesseract path
    pytesseract.pytesseract.tesseract_cmd = stng.TESS_PTH

    # variable to control the current operations of the program
    program_mode = 'RAMSGATE'

    # work in the loop of image recognition
    while True:

        try:

            # pause between captures
            time.sleep(1)

            # update overlay and ensure it stays on top
            if stng.OVERLAY_ON:
                overlay.master.update()
                overlay.master.lift()


            # capture the current state of the screen
            screen_grab = pyautogui.screenshot(region=stng.SCRN_REG)


            # read for lobby screen if last seen in ramsgate
            # ===========================================================================
            if program_mode == 'RAMSGATE':

                # reset error count on return to ramsgate mode
                error_count = 0

                # check for lobby screen
                program_mode, target_name = lobby_detect(screen_grab)

                # if no lobby detected, check for bounty drafting
                if program_mode == 'NO_LOBBY':
                    
                    # if bounty screen detected, switch program mode 
                    if cvt.detect_element(screen_grab, stng.BOUNTY_DRAFT_SLC, stng.BOUNTY_DRAFT_IMG):

                        system_message = 'Bounty drafting screen detected, processing...'
                        overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_INFO, overlay_labels)
                        program_mode = 'IN_DRAFT'

                    # otherwise go back to default mode
                    else:
                        program_mode = 'RAMSGATE'


                # if Escalation detected, wait for results screen
                elif program_mode == 'ESCAL':
                    
                    system_message = f'{target_name} lobby detected, awaiting result screen...'
                    overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_SUCCESS, overlay_labels)                    
                    program_mode = 'IN_ESCAL'
                

                # if Hunt detected, proceed to read lobby further
                elif program_mode == 'HUNT':

                    system_message = 'Hunt lobby detected, reading...'
                    overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_INFO, overlay_labels)
                    threat_level, hunt_type = lobby_reader(screen_grab)

                    # determine between a Hunt and a Trial
                    if threat_level <= 17:

                        # inform user if retrieved hunt details are invalid
                        if utils.validate_hunt(threat_level, target_name):

                            system_message = f'Valid hunt detected: {target_name} T{threat_level} {hunt_type}, awaiting loot screen...'
                            overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_SUCCESS, overlay_labels)
                            program_mode = 'IN_HUNT'
                            
                        else:

                            system_message = f'Invalid hunt detected: {target_name} T{threat_level} {hunt_type}, retrying...'
                            overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_WARNING, overlay_labels)
                            program_mode = 'RAMSGATE'

                    else: 

                        system_message = utils.trial_hype_line(threat_level)
                        overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_JEGG, overlay_labels)
                        program_mode = 'IN_TRIAL'


            # if bounty drafting detected, inform the user and proceed to read the screen
            # ===========================================================================
            elif program_mode == 'IN_DRAFT':

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
                loot_status, loot_data = loot_screen_reader(screen_grab, threat_level, hunt_type, target_name, overlay_labels)

                # accept defeat and reset program mode
                if loot_status == 'DEFEAT':

                    system_message = 'DEFEAT: The party has been defeated, no data will be submitted.\n'
                    overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_WARNING, overlay_labels)
                    program_mode = 'RAMSGATE'


                # otherwise, if everything is fine, submit data
                elif loot_status == 'OK':

                    for data in loot_data:
                        forms.loot_drop_submit(data)

                    system_message = f'Loot data submitted.\n'
                    overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_SUCCESS, overlay_labels)
                    program_mode = 'RAMSGATE'


                # otherwise, if error occured, retry
                elif loot_status == 'ERROR':

                    # increment error counter
                    error_count += 1
                    
                    # inform the user of retrying and loop back if error threshold not reached
                    if error_count <= 5:

                        system_message = f'WARNING: Expected behemoth {loot_data["lobby_behemoth"]} but found {loot_data["loot_behemoth"]}. Retrying...'
                        overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_WARNING, overlay_labels)
                        program_mode = 'IN_LOOT'
                        time.sleep(error_count)

                    elif error_count > 5:

                        system_message = 'ERROR: Retry limit reached. Data will not be submitted.\n'
                        overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_ERROR, overlay_labels)
                        program_mode = 'RAMSGATE'
                            

            # await escalation summary screen if during escalation mode
            # ===========================================================================
            elif program_mode == 'IN_ESCAL':

                # detect escalation summary screen
                if cvt.detect_element(screen_grab, stng.ESCAL_SUMM_SLC, stng.ESCAL_SUMM_IMG):

                    system_message = f'Escalation summary screen detected, processing...'
                    overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_INFO, overlay_labels)
                    program_mode = 'IN_ESCAL_SUMM'


            # process escalation summary screen
            # ===========================================================================
            elif program_mode == 'IN_ESCAL_SUMM':

                # read rank of final escalation round
                summ_slice = stng.ESCAL_RANK_SLC_13 if 'Escalation 1-13' in target_name else stng.ESCAL_RANK_SLC_50
                escal_rank = cvt.read_escalation_rank(screen_grab, summ_slice)


                # if last round was not passed
                if escal_rank == '-':

                    system_message = 'Escalation failed, data will not be submitted.\n'
                    overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_WARNING, overlay_labels)
                    program_mode = 'RAMSGATE'

                # if valid rank was read
                elif escal_rank in ['S', 'A', 'B', 'C', 'D', 'E']:

                    system_message = f'Escalation successful with final round rank {escal_rank}, awaiting loot screen...'
                    overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_SUCCESS, overlay_labels)
                    program_mode = 'WAIT_ESCAL_LOOT'

                # if invalid rank was read
                else:

                    # increment error counter
                    error_count += 1
                    
                    # inform the user of retrying and loop back if error threshold not reached
                    if error_count <= 5:

                        system_message = f'WARNING: Invalid Escalation rank {escal_rank} detected. Retrying...'
                        overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_WARNING, overlay_labels)
                        program_mode = 'IN_ESCAL_SUMM'
                        time.sleep(error_count)

                    elif error_count > 5:

                        system_message = 'WARNING: Retry limit reached. Data will not be submitted.\n'
                        overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_ERROR, overlay_labels)
                        program_mode = 'RAMSGATE'


            # await loot screen if passed escalation summary screen
            # ===========================================================================
            elif program_mode == 'WAIT_ESCAL_LOOT':

                # read loot screen if available
                if cvt.detect_element(screen_grab, stng.LOOT_SLC, stng.LOOT_IMG, prec=0.7):

                    system_message = f'Escalation loot screen detected, processing...'
                    overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_INFO, overlay_labels)
                    program_mode = 'IN_ESCAL_LOOT'


            # read escalation loot data if in loot screen
            # ===========================================================================
            elif program_mode == 'IN_ESCAL_LOOT':

                # the only way to detect error (someone skipping loot accidentally) is to check for this piece
                if cvt.detect_element(screen_grab, stng.LOOT_SLC, stng.LOOT_IMG, prec=0.7):

                    system_message = f'Valid screenshot captured, you may leave the current screen.'
                    overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_INFO, overlay_labels)

                    # read the loot screen
                    loot_data = loot_drops_reader(screen_grab, target_name, target_name, target_name[-2:], target_name)

                    for data in loot_data:
                        forms.loot_drop_submit(data)

                    system_message = system_message = f'Loot data submitted.\n'
                    overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_SUCCESS, overlay_labels)
                    program_mode = 'RAMSGATE'

                # error if we can't establish loot screen anymore
                else:

                    # increment error counter
                    error_count += 1
                    
                    # inform the user of retrying and loop back if error threshold not reached
                    if error_count <= 5:

                        system_message = f"WARNING: Can't access loot data. Retrying..."
                        overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_WARNING, overlay_labels)
                        program_mode = 'IN_ESCAL_LOOT'
                        time.sleep(error_count)

                    elif error_count > 5:

                        system_message = 'ERROR: Retry limit reached. Data will not be submitted.\n'
                        overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_ERROR, overlay_labels)
                        program_mode = 'RAMSGATE'
                        

        # log any exceptions encountered by the program
        except Exception:
            stng.LOG.exception('An exception has occured: ')

'''
Standard stuff, run main function if running the file
'''
if __name__ == '__main__':
    main()