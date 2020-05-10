import string
import random

from datetime import datetime
from settings import HUNT



'''
Helper function
Receives threat level, returns hunt tier associated with it
'''
def get_hunt_tier(threat_level):

    if threat_level <= 7:
        return 'Neutral/Elemental'
    elif threat_level <= 12:
        return 'Dire'
    elif threat_level <= 16:
        return 'Heroic'
    elif threat_level == 17:
        return 'Heroic+'
    elif threat_level == 18:
        return 'Normal Trial'
    elif threat_level == 22:
        return 'Dauntless Trial'
    else:
        return 'ERROR'


'''
Helper function
Receives EXP value of a bounty, returns bounty tier associated with it
'''
def get_bounty_tier(bounty_reward):

    if bounty_reward == 'x20':
        return 'Bronze'
    elif bounty_reward == 'x40':
        return 'Silver'
    elif bounty_reward == 'x100':
        return 'Gold'
    else:
        return 'ERROR'


'''
Simple function that wraps up all the processing applicable to behemoth name
to reduce it to the basic "species".
'''
def trim_behemoth_name(name):

    # remove newlines present because of two-line formatting of heroic namnes
    name = name.replace('\n', ' ')

    # remove heroic classification as it is useless
    name = name.replace(' (Heroic)', '')

    # remove Patrol because we handle the name based on behemoth or element name alone
    name = name.replace(' Patrol', '')

    # split the name into a vector
    name_vec = name.split(' ')

    # if party is not defeated, return where the name should be
    if name_vec[0] != 'Defeated':
        
        # counteract possible trash strings
        # at the end of the read string
        if len(name_vec) >= 2:
            return name_vec[1]
        else:
            return name_vec[0]

    # if party is defeated, pass tha  on
    else:
        return name_vec[0]


'''
When provided with threat level and a behemoth name, the function will return
a boolean value determining if these parametres are those of a valid hunt
'''
def validate_hunt(hunt_data):

    if hunt_data['behemoth'] in HUNT.keys():
        if hunt_data['threat'] in HUNT[hunt_data['behemoth']]:
            return True
    
    return False


'''
Easter egg function
Returns a random text line to hype a player before trials
Mixes in less encouraging lines for Dauntless trials, to mess with people
'''
def trial_hype_line(threat_level):

    target_name = 'Dauntless Trial' if threat_level == 22 else 'Normal Trial'

    hype_lines = [
        'You got it, skipper!',
        "Don't even need a silver sword for this one!"
        ]

    if threat_level == 22:

        hype_lines = [
            *hype_lines,
            'May the Gods have mercy upon your soul.',
            'Abandon hope all ye who enter here.'
            ]

    return f'{target_name} detected. {random.choice(hype_lines)}'


'''
Easter egg function
Returns a random text line to celebrate player victory in trials
Mixes in more weary and less happy lines for Dauntless trials
'''
def trial_victory_line(threat_level):

    victory_lines = [
        'Executed with impunity!',
        'The bigger the beast, the greater the glory.'
    ]

    if threat_level == 22:

        victory_lines = [
            *victory_lines,
            'Battered. Bruised. Victorious.'
        ]

    return random.choice(victory_lines)


'''
Easter egg function
Returns a random defeat line mourning player loss in trials
Mixes in less charitable ones for Dauntless trials
'''
def trial_defeat_line(threat_level):

    defeat_lines = [
        'Sometimes the hero dies in the end. Just ask War.',
        'You either die a Recruit, or live long enough to become a Slayer.'
    ]

    if threat_level == 22:

        defeat_lines = [
            *defeat_lines,
            'More dust, more ashes, more disappointment.',
            'Y O U   D I E D',
        ]

    return random.choice(defeat_lines)