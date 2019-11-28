import time
import pytesseract
import settings as stng

from token_cv import *
from utils import *
from forms import *


'''
Helper function which wraps all the lobby image detection and OCR under one name, 
to clean up the main file code a little
'''
def lobby_reader(screen_grab):

    threat_level = -1
    hunt_type = ''
    behemoth_name = ''
    
    # determine the hunt only if we see the lobby
    if detect_element(screen_grab, stng.LOBBY_SLC, stng.LOBBY_IMG):

        stng.LOG.info('Lobby detected, processing...')

        threat_level = read_threat_level(screen_grab, stng.THRT_SLC)
        hunt_type = 'Patrol' if detect_element(screen_grab, stng.HTYPE_SLC, stng.HTYPE_IMG) else 'Pursuit'

        # determine behemoth name
        behemoth_name = read_behemoth(screen_grab, stng.BHMT_LOBBY_SLC, inverse=True, tess_config=stng.TESS_CONF)
        behemoth_name = trim_behemoth_name(behemoth_name)

        # inform user if retrieved hunt details are invalid
        if not verify_hunt(threat_level, behemoth_name):
            stng.LOG.info(f'Invalid hunt detected: {behemoth_name} T{threat_level} {hunt_type}, retrying...')
        else:
            stng.LOG.info(f'Valid hunt detected: {behemoth_name} T{threat_level} {hunt_type}, awaiting loot screen...')

    return threat_level, hunt_type, behemoth_name


'''
Helper function which wraps all the loot image detection and OCR under one name,
to clean up the main file code a little
'''
def loot_reader(screen_grab, threat_level, hunt_type, behemoth_name):

    # proceed further only if loot screen is detected
    if detect_element(screen_grab, stng.LOOT_SLC, stng.LOOT_IMG, prec=0.7):

        stng.LOG.info(f'Loot screen detected, processing...')

        # determine if we had a token drop
        if_drop = 'Yes' if detect_element(screen_grab, stng.TOKEN_SLC, stng.TOKEN_IMG, prec=0.95) else 'No'

        # determine hunt category
        hunt_tier = get_hunt_tier(threat_level)

        loot_behemoth_name = read_behemoth(screen_grab, stng.BHMT_LOOT_SLC, tess_config=stng.TESS_CONF)
        loot_behemoth_name = trim_behemoth_name(loot_behemoth_name)

        if behemoth_name == loot_behemoth_name:

            # send data to Forms
            fill_basic_form(if_drop, hunt_tier, stng.GAME_VER)
            fill_rich_form(if_drop, hunt_type, hunt_tier, threat_level, behemoth_name, stng.GAME_VER, stng.USER)

            # open log file
            stng.LOG.info(f'Submitted data: {if_drop} - {hunt_type} - {hunt_tier} - {threat_level} - {behemoth_name} - {stng.GAME_VER} - {stng.USER}')

            return 'OK'
        
        else:
            stng.LOG.info(f'WARNING: Expected behemoth {behemoth_name} but found {loot_behemoth_name}. Retrying...')
            return 'ERROR'

    return 'NO_SCREEN'


'''
When provided with threat level and a behemoth name, the function will return
a boolean value determining if these parametres are those of a valid hunt
'''
def verify_hunt(threat_level, behemoth_name):

    if behemoth_name in stng.HUNT.keys():
        if threat_level in stng.HUNT[behemoth_name]:
            return True
    
    return False
    

'''
Bread and butter of the program, running in a loop to continously
read the screen of the user, in order to recover data and process
data collecting efforts
'''
def main():

    # configure tesseract path
    pytesseract.pytesseract.tesseract_cmd = stng.TESS_PTH

    # store lobby variables
    threat_level = ''
    hunt_type = ''
    behemoth_name = ''
    valid_hunt = False
    error_count = 0

    # work in the loop of image recognition
    while True:

        try:

            # pause between captures
            time.sleep(1)

            # capture the current state of the screen
            screen_grab = region_grabber(stng.SCRN_REG)


            # search for new hunt details only if current are invalid
            if not valid_hunt:

                # process lobby visual data
                threat_level, hunt_type, behemoth_name = lobby_reader(screen_grab) 
                valid_hunt = verify_hunt(threat_level, behemoth_name)


            # only attempt detecting loot if hunt is valid
            if valid_hunt:

                # process loot screen visual data
                status = loot_reader(screen_grab, threat_level, hunt_type, behemoth_name)

                # if an error has been detected, increment error counter
                if status == 'ERROR':
                    error_count += 1
                    time.sleep(2)

                # inform user of abandoning the process if retry limit reached
                if error_count == 10:
                    stng.LOG.info('WARNING: Retry limit reached. Data will not be submitted.')
    
                # reset variable on successful form submission or retry limit
                if status == 'OK' or error_count == 5:

                    threat_level = ''
                    hunt_type = ''
                    behemoth_name = ''
                    valid_hunt = False
                    error_count = 0

        # log any exceptions encountered by the program
        except Exception:

            stng.LOG.exception('An exception has occured: ')


'''
Standard stuff, run main function if running the file
'''
if __name__ == '__main__':
    main()