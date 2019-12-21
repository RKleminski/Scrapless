import time
import pytesseract
import settings as stng
import tkinter


from fuzzywuzzy import fuzz, process
from token_cv import *
from utils import *
from forms import *


'''
Detects the lobby and determines the type of a lobby the player is currently in
Additionally returns the name of the "target"
'''
def lobby_detect(screen_grab):

    # determine the hunt only if we see the lobby
    if detect_element(screen_grab, stng.LOBBY_SLC, stng.LOBBY_IMG):

        # check if escalation lobby
        escalation_level = read_escalation_level(screen_grab, stng.ESCAL_LOBBY_SLC)

        if escalation_level != '':
            escalation_level = process.extractOne(escalation_level, ['Escalation 1-13', 'Escalation 10-50'], scorer=fuzz.ratio, score_cutoff=90)

            # return escalation mode and name
            if escalation_level != None:
                return 'ESCAL', escalation_level[0]

        # determine behemoth name if method didn't exit with escalation level
        behemoth_name = read_behemoth(screen_grab, stng.BHMT_LOBBY_SLC, tess_config=stng.TESS_CONF)
        behemoth_name = trim_behemoth_name(behemoth_name)
        behemoth_name = fuzzy_behemoth(behemoth_name)

        return 'HUNT', behemoth_name

    return 'RAMSGATE', ''

'''
Helper function which wraps all the lobby image detection and OCR under one name, 
to clean up the main file code a little
'''
def lobby_reader(screen_grab):

    # read threat level and hunt type
    threat_level = read_threat_level(screen_grab, stng.THRT_SLC)
    hunt_type = 'Patrol' if detect_element(screen_grab, stng.HTYPE_SLC, stng.HTYPE_IMG) else 'Pursuit'

    return threat_level, hunt_type

'''
Detects if the loot screen is visible, and returns appropriate program mode if so
Otherwise, returns the old mode, so program continues operation
'''
def loot_detect(screen_grab, program_mode):

    # proceed further only if loot screen is detected
    if detect_element(screen_grab, stng.LOOT_SLC, stng.LOOT_IMG, prec=0.7):
        return 'LOOT_SCREEN'
    
    else:
        return program_mode

'''
Helper function which wraps all the loot image detection and OCR under one name,
to clean up the main file code a little
'''
def loot_reader(screen_grab, threat_level, hunt_type, behemoth_name):

    # determine if we had a token drop
    if_drop = 'Yes' if detect_element(screen_grab, stng.TOKEN_SLC, stng.TOKEN_IMG, prec=0.95) else 'No'

    # determine hunt category
    hunt_tier = get_hunt_tier(threat_level)

    # read the behemoth name on screen
    loot_behemoth_name = read_behemoth(screen_grab, stng.BHMT_LOOT_SLC, inverse=True, tess_config=stng.TESS_CONF)
    loot_behemoth_name = trim_behemoth_name(loot_behemoth_name)

    # finish early if the party has been defeated 
    if loot_behemoth_name == 'Defeated':
        return 'DEFEAT', {}

    # fuzzy match behemoth name to account for small OCR errors
    loot_behemoth_name = fuzzy_behemoth(loot_behemoth_name)

    # check for expected behemoth name and progress accordingly
    if behemoth_name == loot_behemoth_name:
        
        loot_data = {
            'drop': if_drop,
            'hunt_type': hunt_type,
            'hunt_tier': hunt_tier,
            'threat_level': threat_level,
            'behemoth_name': behemoth_name,
            'patch_ver': stng.GAME_VER,
            'user': stng.USER
        }

        return 'OK', loot_data
    else:
        return 'ERROR', {'lobby_behemoth': behemoth_name, 'loot_behemoth': loot_behemoth_name}

'''
Processes loot data from escalation loot screen
and returns appropriate status once done
'''
def escal_loot_reader(screen_grab, escalation_tier):
    
    # determine if we had a token drop
    if_drop = 'Yes' if detect_element(screen_grab, stng.TOKEN_SLC, stng.TOKEN_IMG, prec=0.9) else 'No'

        
    loot_data = {
        'drop': if_drop,
        'hunt_tier': escalation_tier,
        'patch_ver': stng.GAME_VER,
        'user': stng.USER
    }

    return 'OK', loot_data

'''
When provided with threat level and a behemoth name, the function will return
a boolean value determining if these parametres are those of a valid hunt
'''
def validate_hunt(threat_level, behemoth_name):

    if behemoth_name in stng.HUNT.keys():
        if threat_level in stng.HUNT[behemoth_name]:
            return True
    
    return False
    

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


def overlay_setup(overlay_labels):

    # draw new overlay
    line = 'SCRAPLESS'
    color = stng.OVERLAY_COLOR_INFO
    bg_color= stng.OVERLAY_COLOR_BG

    label = tkinter.Label(text=line, font=(stng.OVERLAY_FONT, stng.OVERLAY_FONT_SIZE), fg=color, bg=bg_color)
    overlay_labels.append(label)
    label.pack()

    # configure the overlay according to our needs
    label.master.overrideredirect(True)
    label.master.geometry(f"+{stng.OVERLAY_X}+{stng.OVERLAY_Y}")
    label.master.minsize(500, 20)
    label.master.configure(bg=bg_color)
    label.master.lift()
    label.master.wm_attributes("-topmost", True)
    label.master.wm_attributes("-disabled", True)
    label.master.wm_attributes("-alpha", stng.OVERLAY_TRANSPARENCY)

    # update overlay and ensure it stays on top
    label.master.update()
    label.master.lift()

    return label, overlay_labels


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

    return label, overlay_labels


def system_output(message, color, overlay, overlay_labels):

    if stng.OVERLAY_ON:

        overlay, overlay_labels = overlay_update(message.replace('\n', ''), color, overlay_labels)

    stng.LOG.info(message)

    return overlay, overlay_labels


'''
Bread and butter of the program, running in a loop to continously
read the screen of the user, in order to recover data and process
data collecting efforts
'''
def main():
    
    # store overlay variables
    overlay = ''
    overlay_lines = []
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


            # capture the current state of the screen
            screen_grab = pyautogui.screenshot(region=stng.SCRN_REG)

            # read for lobby screen if last seen in ramsgate
            if program_mode == 'RAMSGATE':

                error_count = 0
                program_mode, target_name = lobby_detect(screen_grab)

                # if Escalation detected, wait for results screen
                if program_mode == 'ESCAL':
                    
                    system_message = f'{target_name} lobby detected, awaiting result screen...'
                    overlay, overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_SUCCESS, overlay, overlay_labels)                    
                    program_mode = 'IN_ESCAL'
                
                # if Hunt detected, proceed to read lobby further
                elif program_mode == 'HUNT':

                    stng.LOG.info('Hunt lobby detected, reading...')
                    threat_level, hunt_type = lobby_reader(screen_grab)

                    # inform user if retrieved hunt details are invalid
                    if validate_hunt(threat_level, target_name):

                        system_message = f'Valid hunt detected: {target_name} T{threat_level} {hunt_type}, awaiting loot screen...'
                        overlay, overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_SUCCESS, overlay, overlay_labels)
                        program_mode = 'IN_HUNT'

                    else:

                        system_message = f'Invalid hunt detected: {target_name} T{threat_level} {hunt_type}, retrying...'
                        overlay, overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_WARNING, overlay, overlay_labels)
                        program_mode = 'RAMSGATE'


            # await loot screen if currently in a regular hunt
            elif program_mode == 'IN_HUNT':

                program_mode = loot_detect(screen_grab, program_mode)

                # read loot screen if available
                if program_mode == 'LOOT_SCREEN':

                    system_message = f'Loot screen detected, processing...'
                    overlay, overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_INFO, overlay, overlay_labels)
                    loot_status, loot_data = loot_reader(screen_grab, threat_level, hunt_type, target_name)

                    # accept defeat and reset program mode
                    if loot_status == 'DEFEAT':

                        system_message = 'DEFEAT: The party has been defeated, no data will be submitted.\n'
                        overlay, overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_WARNING, overlay, overlay_labels)
                        program_mode = 'RAMSGATE'

                    # otherwise, if everything is fine, submit data
                    elif loot_status == 'OK':

                        if int(loot_data['threat_level']) == 1:

                            system_message = 'INFO: Insufficient threat level detected. Data will not be submitted.'
                            overlay, overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_WARNING, overlay, overlay_labels)
                            program_mode = 'RAMSGATE'

                        elif int(loot_data['threat_level']) > 1:

                            fill_basic_form(loot_data)
                            fill_rich_form(loot_data)

                            system_message = f'Submitted data: {" - ".join(loot_data.values())}\n'
                            overlay, overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_SUCCESS, overlay, overlay_labels)
                            program_mode = 'RAMSGATE'

                    # otherwise, if error occured, retry
                    elif loot_status == 'ERROR':

                        # increment error counter
                        error_count += 1
                        
                        # inform the user of retrying and loop back if error threshold not reached
                        if error_count <= 5:

                            system_message = f'WARNING: Expected behemoth {loot_data["lobby_behemoth"]} but found {loot_data["loot_behemoth"]}. Retrying...'
                            overlay, overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_WARNING, overlay, overlay_labels)
                            program_mode = 'IN_HUNT'
                            time.sleep(error_count)

                        elif error_count > 5:

                            system_message = 'WARNING: Retry limit reached. Data will not be submitted.\n'
                            overlay, overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_ERROR, overlay, overlay_labels)
                            program_mode = 'RAMSGATE'


            # await escalation summary screen if during escalation mode
            elif program_mode == 'IN_ESCAL':

                # detect escalation summary screen
                program_mode = 'ESCAL_SUMM' if detect_element(screen_grab, stng.ESCAL_SUMM_SLC, stng.ESCAL_SUMM_IMG) else 'IN_ESCAL'


                # process escalation summary screen
                if program_mode == 'ESCAL_SUMM':

                    system_message = f'Escalation summary screen detected, processing...'
                    overlay, overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_INFO, overlay, overlay_labels)

                    # read rank of final escalation round
                    escal_rank = read_escalation_rank(screen_grab, stng.ESCAL_RANK_SLC)

                    # if last round was not passed
                    if escal_rank == '-':

                        system_message = 'Escalation failed, data will not be submitted.\n'
                        overlay, overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_WARNING, overlay, overlay_labels)

                    # if valid rank was read
                    elif escal_rank in ['S', 'A', 'B', 'C', 'D', 'E']:

                        system_message = f'Escalation successful with final round rank {escal_rank}, awaiting loot screen...'
                        overlay, overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_SUCCESS, overlay, overlay_labels)
                        program_mode = 'ESCAL_LOOT'

                    # if invalid rank was read
                    else:

                        # increment error counter
                        error_count += 1
                        
                        # inform the user of retrying and loop back if error threshold not reached
                        if error_count <= 5:

                            system_message = f'WARNING: Invalid Escalation rank {escal_rank} detected. Retrying...'
                            overlay, overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_WARNING, overlay, overlay_labels)
                            program_mode = 'IN_ESCAL'
                            time.sleep(error_count)

                        elif error_count > 5:

                            system_message = 'WARNING: Retry limit reached. Data will not be submitted.\n'
                            overlay, overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_ERROR, overlay, overlay_labels)
                            program_mode = 'RAMSGATE'


            # await loot screen if passed escalation summary screen
            elif program_mode == 'ESCAL_LOOT':

                program_mode = loot_detect(screen_grab, program_mode)

                # read loot screen if available
                if program_mode == 'LOOT_SCREEN':

                    system_message = f'Escalation loot screen detected, processing...'
                    overlay, overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_SUCCESS, overlay, overlay_labels)

                    # read the loot screen
                    loot_status, loot_data = escal_loot_reader(screen_grab, target_name)

                    if loot_status == 'OK':
                        
                        fill_basic_form(loot_data)
                        system_message = f'Submitted data: {" - ".join(loot_data.values())}\n'
                        overlay, overlay_labels = system_output(system_message, stng.OVERLAY_COLOR_SUCCESS, overlay, overlay_labels)
                        program_mode = 'RAMSGATE'


        # log any exceptions encountered by the program
        except Exception:
            stng.LOG.exception('An exception has occured: ')

'''
Standard stuff, run main function if running the file
'''
if __name__ == '__main__':
    main()