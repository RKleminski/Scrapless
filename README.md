# Scrapless
Python script for automated data collection on Dauntless Bounty Tokens

# Setup

1. Install the newest version of Tesseract (available [here](https://github.com/UB-Mannheim/tesseract/wiki))
2. Download the repository, or pre-built executable from the releases page
3. Open `config.json` located in `/scrapless/data/json/` and fill in the following:

    a) Provide your nickname in the field `name` of `user` section of the config. This is stored for future time-series analysis and other per-user statistics. If you do not wish to be identifiable, leaving this field empty will prompt Scrapless to fill it with a random ID composed of 20 characters. It would be of great help if you used this exact ID in the future, even after migrating to newer versions of the program
    
    b) In the `paths` section of the config, add the path to your *Dauntless* folder in the `game` field (eg. `"game": "E:/Epic Games/Dauntless",`). This is necessary for the program to access game's current patch version
    
    c) In the same `paths` section, verify that the path leading to `tesseract.exe` is correct
    
# Usage

When you intend to play *Dauntless*, simply run *Scrapless* and let it do its work. Console output will inform you about the current operation of the program. In some unforeseen circumstances, it might be necessary to restart the program to ensure its continued operation.

# Bugs and issues

Report them here, or contact me directly through social media handles mentioned when sharing the link to this repository.
