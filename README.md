# Scrapless
Python script for automated data collection on Dauntless Bounty Tokens

# Setup

1. Install the newest version of Tesseract (available [here](https://github.com/UB-Mannheim/tesseract/wiki))
2. Download the repository, or pre-built executable from the [releases](https://github.com/RKleminski/Scrapless/releases) page
3. Open `config.json` located in `/scrapless/data/json/` and fill in the following:

    a) Provide your nickname in the field `name` of `user` section of the config. This is stored for future time-series analysis and other per-user statistics. If you do not wish to be identifiable, leaving this field empty will prompt Scrapless to fill it with a random ID composed of 20 characters. It would be of great help if you used this exact ID in the future, even after migrating to newer versions of the program
    
    b) In the `paths` section of the config, add the path to your *Dauntless* folder in the `game` field (eg. `"game": "E:/Epic Games/Dauntless",`). This is necessary for the program to access game's current patch version
    
    c) In the same `paths` section, verify that the path leading to `tesseract.exe` is correct
    
# Usage

When you intend to play *Dauntless*, simply run *Scrapless* and let it do its work. Console output will inform you about the current operation of the program. In some unforeseen circumstances, it might be necessary to restart the program to ensure its continued operation.

# What does it actually do?

The idea behind Scrapless is simple: it uses image recognition and Optical Character Recognition (reading text off images) to automatically gather the data off your screen as you play. This is achieved by a loop of operations:

1. Once started, Scrapless will begin taking snapshots of your main monitor every second. This delay can grow longer, as it starts after all current image processing has concluded.

    a) What is your main monitor? On Windows systems (which you have to use to play Dauntless) it is the one where all games will run by default, and which has a more fully fledged Task Bar. You can always check which screen is your main in system settings.

2. In the event of Airship Lobby being found on the screenshot, it a few quick procedures will be launched to get hunt type (Patrol/Pursuit), Behemoth name and Threat Level. These are saved to memory for later use. Until the hunt concludes, this part of the program won't run anymore.

3. In the event of Loot screen being detected, the program will again retrieve behemoth name, along with information on whether or not the token appears in the loot (they always take the top spot, making this task easy). From there one, one of the following happens:

    a) All data is correct, and the program will submit it through designated GoogleForms, then purge its memory and look for another Lobby screen.

    b) Player party was defeated, data is not submitted, and its purged.

    c) There is a mismatch between behemoth names, causing the program to re-try the procedure five more times, in three second intervals (in case it was attempting to read the screen at an inopportune time). If the retry limit is reached, data won't be submitted and will be purged.

# Bugs and issues

Report them here, or contact me directly through social media handles mentioned when sharing the link to this repository.

Current issues and limitations:
* Program works with 1920x1080p resolution only (fullscreen or borderless fullscreen)
