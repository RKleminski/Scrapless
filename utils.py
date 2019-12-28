import string
import random

from datetime import datetime
from settings import HUNT



'''
Helper function
Receives threat level, returns hunt tier associated with it
'''
def get_hunt_tier(threat_level):

    threat_level = int(threat_level)

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

    name = name.replace(' (Heroic)', '')
    name_vec = name.split(' ')

    if name_vec[0] != 'Defeated':
        return name_vec[-1]
    else:
        return name_vec[0]


'''
When provided with threat level and a behemoth name, the function will return
a boolean value determining if these parametres are those of a valid hunt
'''
def validate_hunt(threat_level, behemoth_name):

    if behemoth_name in HUNT.keys():
        if threat_level in HUNT[behemoth_name]:
            return True
    
    return False


'''
Easter egg function
Returns a random text line to hype a player before trials
Mixes in less encouraging lines for Dauntless trials, to mess with people
'''
def trial_hype_line(threat_level):

    hype_lines = [
        'You got it, skipper!',
        'First stagger to the right, and straight on till victory!',
        "Don't even need a silver sword for this one!"
        ]

    if threat_level == '22':

        hype_lines = [
            *hype_lines,
            'May the Gods have mercy upon your soul.',
            'Abandon hope all ye who enter here.'
            ]

    return f'{get_hunt_tier(threat_level)} detected. {random.choice(hype_lines)}'


'''
Easter egg function
Returns a random text line to celebrate player victory in trials
Mixes in more weary and less happy lines for Dauntless trials
'''
def trial_victory_line(threat_level):

    victory_lines = [
        'Executed with impunity!',
        'Another abomination cleansed from our lands.',
        'The bigger the beast, the greater the glory.'
    ]

    if threat_level == '22':

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
        'Y O U   D I E D',
        'You either die a Recruit, or live long enough to become a Slayer'
    ]

    if threat_level == '22':

        defeat_lines = [
            *defeat_lines,
            'More dust, more ashes, more disappointment.',
        ]

    return random.choice(defeat_lines)