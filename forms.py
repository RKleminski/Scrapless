import requests, warnings
import urllib.request
import time

# in_url = 'https://docs.google.com/forms/d/e/1FAIpQLSfqaV4JbwTrLRXdD9SLFny6D_cXZCgWqa5L6J-PSgLsVYb36Q/viewform'

# res = urllib.request.urlopen(in_url)
# soup = BeautifulSoup(res.read(), 'html.parser')
# get_names = lambda f: [v for k,v in f.attrs.items() if 'label' in k]
# get_name = lambda f: get_names(f)[0] if len(get_names(f))>0 else 'unknown'
# all_questions = soup.form.findChildren(attrs={'name': lambda x: x and x.startswith('entry.')})

# #{get_name(q): q['name'] for q in all_questions}

# print({get_name(q): q['name'] for q in all_questions})


'''
A function to submit the data to the basic data-gathering Form
This supplies only a binary token-drop information, along with 
hunt category and patch version of the game

More nuanced data is withheld here, and kept for the second, more
detailed form
'''
def fill_basic_form(if_token_drop, hunt_category, patch_version):

    # address to the basic data collection form
    url = 'https://docs.google.com/forms/d/e/1FAIpQLSdqFcIsscHN6lgNi3mP2Z1_MW0PlpLGG2trsznf19tL0lPnig/formResponse'
    
    # prepare response data
    form_data = {"entry.363103481": if_token_drop, 
                 "entry.936871560": hunt_category, 
                 "entry.985493627": patch_version,
                 "draftResponse":'[]',
                 "pageHistory":0
                 }
    
    # send the request and return a response
    return requests.post(url, data=form_data)


'''
A function to submit the data to the expanded data-gathering Form
'''
def fill_rich_form(if_token_drop, hunt_type, hunt_tier, threat_level, behemoth_name, patch_version, user):

    # address to the basic data collection form
    url = 'https://docs.google.com/forms/d/e/1FAIpQLSfqaV4JbwTrLRXdD9SLFny6D_cXZCgWqa5L6J-PSgLsVYb36Q/formResponse'
    
    # prepare response data
    form_data ={
        'entry.114724379': if_token_drop,
        'entry.250442381': hunt_type,
        'entry.1693875264': hunt_tier,
        'entry.987397251': threat_level,
        'entry.686667836': behemoth_name,
        'entry.668337464': patch_version,
        'entry.1430591986': user,
        'draftResponse': [],
        'pageHistory': 0
        }

    # send the request and return a response
    return requests.post(url, data=form_data)