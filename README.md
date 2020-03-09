# Scrapless
Python script for automated data collection on Dauntless Bounty Tokens and Dauntless Bounty Rarities.
The spreadsheet which tracks all the results and computes statistics is vailablee [here](https://docs.google.com/spreadsheets/d/1wtdNR_wwfzliNhLvSw0MW-yoDe4uhLDuPJ0mL1y1Gps/edit#gid=1171610346)

# Requirements

1. You must be running the game in 1920x1080 resolution, either Fullscreen or Borderless Fullscreen.
2. Borderless Fulscreen is required to have the overlay working.

# Setup

## 1. Installation

1. Install the newest version of Tesseract (available [here](https://github.com/UB-Mannheim/tesseract/wiki))
2. Download the repository, or pre-built executable from the [releases](https://github.com/RKleminski/Scrapless/releases) page

## 2. Configuration

1. Open `config.json` located in `/scrapless/data/json/`

2. Provide your nickname in the field `name` of `user` section of the config:

    a) This is stored for future time-series analysis and other per-user statistics. 
    
    b) If you do not wish to be identifiable, leaving this field empty will prompt Scrapless to fill it with a random ID composed of 20 characters. It would be of great help if you used this exact ID in the future, even after migrating to newer versions of the program.

3.  Provide necessary paths in the `paths` section of the file:

    a) Add the path to your *Dauntless* folder in the `game` field (eg. `"game": "E:/Epic Games/Dauntless",`). This is necessary for the program to access game's current patch version.
    
    b) In the `tesseract` field, verify that the path leading to *tesseract.exe* is correct. 
    
4. Leave the `screen` section untouched. This part of the configuration is there for the future development.

5. Configure the `overlay`:

    a) You can completely disable the overlay by filling "No" in `enable` field.
    
    b) `opacity` is a numeric value describing how transparent the overlay background and output should be. For example, 65 means 65% opacity.
    
    c) `position` provides screen coordinates for the upper left corner of the overlay. Be advised that the overlay is 500px wide, while its height is determined by `font-size` and `max_lines`.
    
    d) `max_lines` sets a cap of how many output lines the overlay will show. All output is pushed to the console regardless.
    
    e) `font` sets the font to use in the output.
    
    f) `font_size` determines font size on the overlay.
    
    g) All fields in the `colors` section determine the colors of specific types of output lines and the background of the overlay. You can change them according to your wish. All colours are provided as HEX codes.
    
# Usage

When you intend to play *Dauntless*, simply run *Scrapless* and let it do its work. Console output and overlay will inform you about the current operation of the program. In some unforeseen circumstances, it might be necessary to restart the program to ensure its continued operation.

Please read the list below to know which screens are of interest for *Scrapless*, and ensure that you give it a couple seconds on each of those to perform its magic. Data collection is for the patient.

# What does it actually do?

The idea behind Scrapless is simple: it uses image recognition and Optical Character Recognition (reading text off images) to automatically gather the data off your screen as you play. This is achieved by a loop of operations:

1. Once started, Scrapless will begin taking snapshots of your main monitor every second. This delay can grow longer, as it starts after all current image processing has concluded. What is your main monitor? On Windows systems (which you have to use to play Dauntless) it is the one where all games will run by default, and which has a more fully fledged Task Bar. You can always check which screen is your main in system settings.

2. *Scrapless* will detect the Airship Lobby of any type of hunt and read the screen for Behemoth name, Threat level and Patrol/Pursuit type of a hunt.

3. In case of Escalation, the program has to first verify that you beat the last monster available (by reading the final rank). Once that is done, you can move to the Loot screen.

4. On Loot screen, the program will simply try and detect the Bounty Token icon and the drop quantity. Behemoth name is captured once again for verification purposes (for non-Escalation hunts).

5. *Scrapless* will also detect that you are drafting a Bounty, and it will log the quality of said Bounty as well.

# Bugs and issues

Report them here, or contact me directly through social media handles mentioned when sharing the link to this repository.

Current issues and limitations:
* Program works with 1920x1080p resolution only (fullscreen or borderless fullscreen)
