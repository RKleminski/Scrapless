import PyInstaller.__main__
from pathlib import Path
import shutil
import json


#
# set scrapless version
scrap_ver = '1.0.1.4'
distpath = Path('./dist')

#
# clear the destination folder
if distpath.exists() and distpath.is_dir():
    shutil.rmtree(distpath)

#
# compile
PyInstaller.__main__.run([
    '--onedir',
    '--noconfirm',
    f'--name=scrapless',
    '--icon=./data/icon/large.ico',
    'scrapless.py'
])


#
# copy data folder
shutil.copytree(src='./data/', dst='./dist/scrapless/data')

#
# blank the user in config file
with open('./dist/scrapless/data/json/config/config.json', 'r') as f:
    conf_json = json.load(f)

# replace username with an empty one
conf_json['user'] = ''

# overwrite the file
with open('./dist/scrapless/data/json/config/config.json', 'w') as f:
    json.dump(conf_json, f, indent=2, separators=(',',':'))


#
# zip the file to prepare it for sharing
shutil.make_archive(f'./dist/scrapless {scrap_ver}', 'zip', './dist/scrapless')


#
# bring back my name in config file
with open('./dist/scrapless/data/json/config/config.json', 'r') as f:
    conf_json = json.load(f)

# replace username with an empty one
conf_json['user'] = 'Roel'

# overwrite the file
with open('./dist/scrapless/data/json/config/config.json', 'w') as f:
    json.dump(conf_json, f, indent=2, separators=(',',':'))