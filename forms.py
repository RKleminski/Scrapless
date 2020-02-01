import requests, warnings
import urllib.request
import time

# from bs4 import BeautifulSoup

# in_url = 'https://docs.google.com/forms/d/e/1FAIpQLSe5D27ExvAlgnrpeaYuxOLit-9w8nBqUIqcx6QtDvGQUgl5dA/viewform'

# res = urllib.request.urlopen(in_url)
# soup = BeautifulSoup(res.read(), 'html.parser')
# get_names = lambda f: [v for k,v in f.attrs.items() if 'label' in k]
# get_name = lambda f: get_names(f)[0] if len(get_names(f))>0 else 'unknown'
# all_questions = soup.form.findChildren(attrs={'name': lambda x: x and x.startswith('entry.')})

# #{get_name(q): q['name'] for q in all_questions}

# print({get_name(q): q['name'] for q in all_questions})


def escalation_form_submit(loot_data):

    # address to the form
    url = 'https://docs.google.com/forms/d/e/1FAIpQLSe5D27ExvAlgnrpeaYuxOLit-9w8nBqUIqcx6QtDvGQUgl5dA/formResponse'

    # prepare response data
    form_data = {
        'entry.1541761150': loot_data['drop_count'],
        'entry.555180002': loot_data['hunt_tier'],
        'entry.1719738408': loot_data['patch_ver'],
        'entry.1439657109': loot_data['user'],
        "draftResponse":'[]',
        "pageHistory":0
    }

    # send the request and return a response
    return requests.post(url, data=form_data)


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
A function to submit the data to the basic data-gathering Form
This supplies only a binary token-drop information, along with 
hunt category and patch version of the game
'''
def token_form_basic_submit(loot_data):

    # address to the basic data collection form
    url = 'https://docs.google.com/forms/d/e/1FAIpQLSdqFcIsscHN6lgNi3mP2Z1_MW0PlpLGG2trsznf19tL0lPnig/formResponse'
    
    # prepare response data
    form_data = {"entry.363103481": loot_data['drop'], 
                 "entry.936871560": loot_data['hunt_tier'], 
                 "entry.985493627": loot_data['patch_ver'],
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
def token_form_rich_submit(loot_data):

    # address to the basic data collection form
    url = 'https://docs.google.com/forms/d/e/1FAIpQLSfqaV4JbwTrLRXdD9SLFny6D_cXZCgWqa5L6J-PSgLsVYb36Q/formResponse'
    
    # prepare response data
    form_data ={
        'entry.114724379': loot_data['drop'],
        'entry.250442381': loot_data['hunt_type'],
        'entry.1693875264': loot_data['hunt_tier'],
        'entry.987397251': loot_data['threat_level'],
        'entry.686667836': loot_data['behemoth_name'],
        'entry.668337464': loot_data['patch_ver'],
        'entry.1430591986': loot_data['user'],
        'draftResponse': [],
        'pageHistory': 0
        }

    # send the request and return a response
    return requests.post(url, data=form_data)