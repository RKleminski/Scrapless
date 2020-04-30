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
def loot_screen_reader(screen_grab,hunt_data, overlay_labels):

    # read the behemoth name on screen
    loot_behemoth_name = cvt.read_behemoth(screen_grab, stng.LOOT_BHMT_SLC, inverse=True, tess_config=stng.TESS_CONF, thresh=100)
    loot_behemoth_name = utils.trim_behemoth_name(loot_behemoth_name)

    # finish early if the party has been defeated 
    if loot_behemoth_name == 'Defeated':
        return 'DEFEAT', {}

    # fuzzy match behemoth name to account for small OCR errors
    loot_behemoth_name = fuzzy_behemoth(loot_behemoth_name)


    # check for expected behemoth name and progress accordingly
    if hunt_data['behemoth'] == loot_behemoth_name or hunt_data['behemoth'] in ['Neutral', 'Blaze', 'Frost', 'Terra', 'Shock', 'Dire', 'Heroic', 'Heroic+']:
        
        system_message = f'Valid screenshot captured, you may leave the current screen.'
        overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_INFO, overlay_labels)

        # overwrite behemoth name
        hunt_data['behemoth'] = loot_behemoth_name

        # determine hunt category
        hunt_data['tier'] = utils.get_hunt_tier(hunt_data['threat'])

        # determine death count
        hunt_data['deaths'] = cvt.read_death_count(screen_grab, stng.LOOT_DEATH_SLC)

        # check for Elite pass
        hunt_data['elite'] = cvt.detect_element(screen_grab, stng.LOOT_ELITE_SLC, stng.ELITE_IMG)

        # read hunt time
        hunt_data['time'] = cvt.read_hunt_time(screen_grab, stng.LOOT_TIME_SLC)

        loot_data = loot_drops_reader(screen_grab, hunt_data)

        return 'OK', loot_data
    else:
        return 'ERROR', {'lobby_behemoth': hunt_data['behemoth'], 'loot_behemoth': loot_behemoth_name}


def loot_drops_reader(screen_grab, hunt_data):

    # retrieve list of possible drops
    drop_list = stng.DROP_LIST[hunt_data['behemoth']]
    
    # add appropriate orbs to the drop list
    if hunt_data['tier'] == 'Neutral/Elemental':
        for orb_name in ['Neutral Orb', 'Shock Orb', 'Blaze Orb', 'Frost Orb', 'Terra Orb']:
            drop_list[orb_name] = 'Common (Orb)'
    if hunt_data['tier'] == 'Dire':
        drop_list['Dull Arcstone'] = 'Uncommon (Orb)'
    if hunt_data['tier'] in ['Heroic', 'Heroic+']:
        drop_list['Shining Arcstone'] = 'Rare (Orb)'

    # determine slay loot roll count
    slay_rolls = 2 + (3 - hunt_data['deaths']) + (2 * hunt_data['elite'])

    # compensate for Elite loot bug
    if hunt_data['tier'] == 'Heroic+' and hunt_data['behemoth'] not in ['Shrowd', 'Rezakiri'] and hunt_data['elite']:
        slay_rolls -= 2

    # array for applicable loot lines
    loot_drops = []
    slay_loot_drops = []


    # loop through areas of loot screen
    for loot_slice in [ stng.LOOT_BASE_SLC, stng.LOOT_BONS_SLC ]:

        # check if part breaks are there
        if cvt.detect_element(screen_grab, stng.LOOT_BASE_SLC, stng.BREAK_IMG, prec=0.9):
                
                # if so, omit them
                part_coord = cvt.locate_element(screen_grab, stng.LOOT_BASE_SLC, stng.BREAK_IMG, prec=0.9)
                loot_slice[1] = loot_slice[0] + part_coord[1]

        # read all text from the area
        loot_lines = cvt.read_loot_section(screen_grab, loot_slice)

        # iterate over read lines
        for line in loot_lines.splitlines():

            # ensure the line has some text
            if line != '' and re.search('[a-zA-Z]', line):

                # get the best cell match to verify if we are operating on a cell
                cell_match = process.extractOne(line.split(' ', 2)[-1], stng.CELL_LIST, scorer=fuzz.ratio, score_cutoff=80)

                # get a cell, if a cell is in the line
                if cell_match is not None:
                    drop = line.split(' ', 2)[-2] + ' ' + cell_match[0]
                # get a fuzzy match to the possible drops otherwise
                else:
                    drop = fuzzy_drop(line.split(" ", 1)[-1], drop_list.keys())

                # proceed with processing if we got a cell or a fuzzy match
                if drop != '':

                    # iteration until we can find the proper count
                    # (this is in case of garbage in front of the string)
                    for iter in range(0, len(line.split(' '))):

                        # take a part of the string
                        count_str = line.split(" ")[iter]

                        # replace symbols we know tend to replace digits
                        for character in stng.CONFUSION_DICT.keys():
                            count_str = count_str.replace(character, stng.CONFUSION_DICT[character])

                        # remove everything that isn't a number
                        count_str = re.sub("[^0-9]", "", count_str[1:])

                        # if we have proper string, jump out
                        if count_str != '':
                            break
                        
                    # get the drop number, omit the first character as it is whatever the program read "x" as
                    count = int(count_str)
                        
                    # handle the number of the orbs
                    if drop in stng.ORB_LIST:

                        # when orbs were rolled together with patrol reward
                        if count > 10 and count % 3 != 0:
                            count -= 10

                        # add non-patrol orbs to loot
                        if count % 3 == 0:
                            for iter in range(0, int(count/3)):
                                loot_drops.append((drop, 3))

                    # drop an error if we don't deal with 
                    # orbs and we had weirdly many drops
                    elif count >= 10:
                        return 'TOO_MANY_DROPS'

                    # handle cell drops
                    elif 'Cell' in drop:

                        cell_pow = drop.split(' ')[0]

                        # replace symbols we know tend to replace digits
                        for character in stng.CONFUSION_DICT.keys():
                            cell_pow = cell_pow.replace(character, stng.CONFUSION_DICT[character])

                        # put the name back together
                        drop = ' '.join([cell_pow, *drop.split(' ')[1:]])

                        # add to slay drops
                        for iter in range(0, count):
                            slay_loot_drops.append((drop, count))


                    # handle non-orb, non-cell drops
                    else:

                        # check single drop count expected through rarity
                        count_div = 2 if drop_list[drop] == 'Epic' else 1

                        # add to drops in appropriate increments
                        for iter in range(0, int(count/count_div)):
                            if drop_list[drop] == 'Artifact (Dye)':
                                slay_loot_drops.append((drop, count_div))
                            else:
                                loot_drops.append((drop, count_div))


    # draw a sample of loot rolls - this counteracts numerous Loot Screen bugs
    num_samples = slay_rolls - len(slay_loot_drops) if len(slay_loot_drops) + len(loot_drops) < 2 * slay_rolls else slay_rolls*2 - len(slay_loot_drops)

    # for safety, never sample for more than all remaining drops
    num_samples = min(num_samples, len(loot_drops))

    # randomly sample the remaining drops
    loot_samples = random.sample(loot_drops, num_samples)

    # add samples to slay drop list
    slay_loot_drops.extend(loot_samples)

    # prepare final loot output
    loot_data = []

    # create an entry for every acquired drop
    for drop in slay_loot_drops:

        name = drop[0]
        count = drop[1]

        loot_row = {
            'hunt_type': hunt_data['type'],
            'hunt_tier': hunt_data['tier'],
            'threat_level': hunt_data['threat'],
            'behemoth_name': hunt_data['behemoth'],
            'patch_ver': stng.GAME_VER,
            'user': stng.USER
        }

        loot_row['drop_count'] = count
        loot_row['drop_name'] = name
        loot_row['drop_rarity'] = ('Uncommon (Cell)' if '+1' in name else 'Rare (Cell)') if 'Cell' in name else drop_list[name]

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


def fuzzy_drop(drop, drop_list):

    if drop in drop_list:
        return drop
    else:
        match = process.extractOne(drop, drop_list, scorer=fuzz.ratio, score_cutoff=80)
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

    # dict for storing hunt data
    hunt_data = {}

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
                program_mode, hunt_data['behemoth'] = lobby_detect(screen_grab)

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
                    
                    system_message = f'{hunt_data["behemoth"]} lobby detected, awaiting result screen...'
                    # overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_SUCCESS, overlay_labels)                    
                    # program_mode = 'IN_ESCAL'
                

                # if Hunt detected, proceed to read lobby further
                elif program_mode == 'HUNT':

                    system_message = 'Hunt lobby detected, reading...'
                    overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_INFO, overlay_labels)
                    hunt_data['threat'], hunt_data['type'] = lobby_reader(screen_grab)

                    # determine between a Hunt and a Trial
                    if hunt_data['threat'] <= 17:

                        # inform user if retrieved hunt details are invalid
                        if utils.validate_hunt(hunt_data):

                            system_message = f'Valid hunt detected: {hunt_data["behemoth"]} T{hunt_data["threat"]} {hunt_data["type"]}, awaiting loot screen...'
                            overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_SUCCESS, overlay_labels)
                            program_mode = 'IN_HUNT'
                            
                        else:

                            system_message = f'Invalid hunt detected: {hunt_data["behemoth"]} T{hunt_data["threat"]} {hunt_data["type"]}, retrying...'
                            overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_WARNING, overlay_labels)
                            program_mode = 'RAMSGATE'

                    else: 

                        system_message = utils.trial_hype_line(hunt_data['threat'])
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
                loot_status, loot_data = loot_screen_reader(screen_grab, hunt_data, overlay_labels)

                # accept defeat and reset program mode
                if loot_status == 'DEFEAT':

                    system_message = 'DEFEAT: The party has been defeated, no data will be submitted.\n'
                    overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_WARNING, overlay_labels)
                    hunt_data = {}
                    program_mode = 'RAMSGATE'

                # otherwise, if suspicious loot numbers, save screenshot for future reference
                elif loot_data == 'TOO_MANY_DROPS':

                    system_message = f'ERROR: Suspiciously big stack of loot. Screenshot saved, data won\'t be submitted.'
                    overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_ERROR, overlay_labels)

                    path = './error_imgs/'
                    if not os.path.exists(path):
                        os.makedirs(path)
                    cv2.imwrite(f'path/{uuid4()}.png', cv2.cvtColor(screen_grab, cv2.COLOR_RGB2BGR))

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
                        hunt_data = {}
                        program_mode = 'RAMSGATE'
                        

        # log any exceptions encountered by the program
        except Exception:
            stng.LOG.exception('An exception has occured: ')

'''
Standard stuff, run main function if running the file
'''
if __name__ == '__main__':
    main()