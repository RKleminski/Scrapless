# Scrapless
Python script for automated data collection on Dauntless Slay Drops and Dauntless Bounty Rarities.
The spreadsheets which tracks all the results and computes statistics are available [here](https://docs.google.com/spreadsheets/d/1wtdNR_wwfzliNhLvSw0MW-yoDe4uhLDuPJ0mL1y1Gps/edit?usp=sharing) and [here](https://docs.google.com/spreadsheets/d/1r1rZQWAa6DmLxfj6ZOe-o-Z6uOP3olP3UMwhcvgFwpk/edit?usp=sharing).

# Requirements

1. You must be running the game in 1920x1080 resolution, either Fullscreen or Borderless Window.
2. Borderless Window is required to have the overlay working.

# Setup

## 1. Installation

1. Install the newest version of Tesseract (available [here](https://github.com/UB-Mannheim/tesseract/wiki))
2. Download the repository or pre-built executable from the [releases](https://github.com/RKleminski/Scrapless/releases) page

## 2. Configuration

1. Open `config.json` located in `/scrapless/data/json/config/`

2. Provide your nickname in the `name` field of the `user` section of the config:

    a) This is stored for future time-series analysis and other per-user statistics. 
    
    b) If you do not wish to be identifiable, leaving this field empty will prompt Scrapless to fill it with a random ID. It would be of great help if you used this exact ID in the future, even after migrating to newer versions of the program.

3. In the `tesseract` field, verify that the path leading to *tesseract.exe* is correct. 
    
4. Configure the `overlay.json` located in `/scrapless/data/json/config/`:

    a) You can completely disable the overlay by filling "No" in `enable` field.
    
    b) `opacity` is a numeric value describing how transparent the overlay background and output should be. For example, 65 means 65% opacity.
    
    c) `max_lines` sets a cap of how many output lines the overlay will show. All output is pushed to the console regardless.
    
    d) `position` provides screen coordinates for the upper left corner of the overlay. Be advised that the overlay is 500px wide, while its height is determined by `font_size` and `max_lines`.
        
    e) `font` sets the font family you want to use, along with font size. Standard modifiers like Bold and Cursive apply
        
    f) All fields in the `colors` section determine the colors of specific types of output lines and the background of the overlay. You can change them according to your wish. All colours are provided as HEX codes.
    
# Usage

When you intend to play *Dauntless*, simply run *Scrapless* in the background and let it do its work. Console output and overlay will inform you about the current operation of the program. In some circumstances, it might be necessary to restart the program to ensure its continued operation.

Please read the list below to know which screens are of interest for *Scrapless*, and ensure that you give it a couple seconds on each of those screens to perform its magic. Data collection is for the patient.

# What does it actually do?

The idea behind Scrapless is simple: it uses image recognition and Optical Character Recognition (reading text off images) to automatically gather the data off your screen as you play. This is achieved by a loop of operations:

1. Once started, Scrapless will begin taking snapshots of your main monitor every second. This delay can grow longer, as it starts after all current image processing has concluded.

	- What is your main monitor? On Windows systems (which you have to use to play Dauntless) it is the one where all games will run by default, and which has a more fully fledged Task Bar. You can always check which screen is your main in system settings.

2. *Scrapless* will detect the Airship Lobby of any type of hunt and read the screen for Behemoth name, Threat level and Patrol/Pursuit type of a hunt.

3. On Loot screen, the program will try to read all eligible Slay drops, and their quantity, from the loot list. Behemoth name is captured once again for verification purposes (for non-Escalation hunts).

	- This is a pretty long process, but the program will inform you as soon as it has captured valid screenshot. The processing can happen in the background, so you can leave the loot screen at that point.

4. In case of Escalation and Trials, the program will detect these, but will not attempt to read loot. This functionality is enabled merely to keep a unified flow of the application and for future expansion. The program will react appropriately to the end of hunt screen after either of these

5. *Scrapless* will also detect when you are drafting a Bounty and it will log the quality of said Bounty as well.

# Bugs and issues

Report them here, or contact me directly through social media handles mentioned when sharing the link to this repository.

Current issues and limitations:
* Program works with 1920x1080p resolution only (fullscreen or borderless fullscreen)
