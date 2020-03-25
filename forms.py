import requests, warnings
import urllib.request
import time

# from bs4 import BeautifulSoup

# in_url = 'https://docs.google.com/forms/d/e/1FAIpQLScQta22u7mNLmW0kYK8AMvvzyH2zV9FJqtHHgrLXII__P_Fmg/viewform'

# res = urllib.request.urlopen(in_url)
# soup = BeautifulSoup(res.read(), 'html.parser')
# get_names = lambda f: [v for k,v in f.attrs.items() if 'label' in k]
# get_name = lambda f: get_names(f)[0] if len(get_names(f))>0 else 'unknown'
# all_questions = soup.form.findChildren(attrs={'name': lambda x: x and x.startswith('entry.')})

# #{get_name(q): q['name'] for q in all_questions}

# print({get_name(q): q['name'] for q in all_questions})


def bounty_form_submit(bounty_data):

    # address to the form
    url = 'https://docs.google.com/forms/d/e/1FAIpQLScPhTXcUeknn3x61lM3eXmuVte22UpDTAHfOMACJyIgPR7HlQ/formResponse'

    # prepare response data
    form_data = {
        'entry.992001393': bounty_data['rarity'],
        'entry.1260286408': bounty_data['patch_ver'],
        'entry.1036986319': bounty_data['user'],
        "draftResponse":'[]',
        "pageHistory":0
    }

    # send the request and return a response
    return requests.post(url, data=form_data)


'''
A function to submit the data to the expanded data-gathering Form
Submits binary token-drop information, type and tier of the hunt,
threat level, behemoth name, patch version and the user
'''
def loot_drop_submit(loot_data):

    # address to the basic data collection form
    url = 'https://docs.google.com/forms/d/e/1FAIpQLScQta22u7mNLmW0kYK8AMvvzyH2zV9FJqtHHgrLXII__P_Fmg/formResponse'
    
    # prepare response data
    form_data ={
        'entry.2041180610': loot_data['drop_count'],
        'entry.1482206842': loot_data['drop_name'],
        'entry.1551997662': loot_data['drop_rarity'],
        'entry.919390435': loot_data['hunt_tier'],
        'entry.1751410986': loot_data['threat_level'],
        'entry.2105670628': loot_data['behemoth_name'],
        'entry.1036773674': loot_data['patch_ver'],
        'entry.1084675089': loot_data['user'],
        'draftResponse': [],
        'pageHistory': 0
        }

    # send the request and return a response
    return requests.post(url, data=form_data)