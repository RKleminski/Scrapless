import string
import random

from datetime import datetime
from settings import HUNT


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