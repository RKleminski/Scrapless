import requests, warnings
import urllib.request
from bs4 import BeautifulSoup

in_url = 'https://docs.google.com/forms/d/e/1FAIpQLSdqFcIsscHN6lgNi3mP2Z1_MW0PlpLGG2trsznf19tL0lPnig/viewform'

res = urllib.request.urlopen(in_url)
soup = BeautifulSoup(res.read(), 'html.parser')
get_names = lambda f: [v for k,v in f.attrs.items() if 'label' in k]
get_name = lambda f: get_names(f)[0] if len(get_names(f))>0 else 'unknown'
all_questions = soup.form.findChildren(attrs={'name': lambda x: x and x.startswith('entry.')})

#{get_name(q): q['name'] for q in all_questions}

url = 'https://docs.google.com/forms/d/e/1FAIpQLSdqFcIsscHN6lgNi3mP2Z1_MW0PlpLGG2trsznf19tL0lPnig/formResponse'
form_data = {"entry.363103481": "No", "entry.936871560": "Dire", "entry.985493627": "1.0.2","draftResponse":'[]',"pageHistory":0}
requests.post(url, data=form_data)