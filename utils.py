import traceback
import inspect
import string
import logging

from datetime import datetime


'''
Helper function designed solely to return hunt tier
for a given threat level. Basic logic, simple functionality
Should possibly move the values to global variables
'''
def get_hunt_tier(threat_level):

    threat_level = int(threat_level)

    if threat_level <= 7:
        return 'Neutral/Elemental'
    elif threat_level <= 12:
        return 'Dire'
    elif threat_level <= 16:
        return 'Heroic'
    elif threat_level <= 22:
        return 'Heroic+'


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