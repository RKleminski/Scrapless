import time

from app import App

from fuzzywuzzy import fuzz, process

def main():

    # new instance of the main class
    scrapless = App()

    # operate in an infinite loop
    while True:

        # capture the screen
        scrapless.screenCap()

        # run processing functions
        scrapless.processScreen()

        # refresh the overlay to keep it responsive, if present
        if scrapless.overlay.enabled:
            scrapless.overlay.refresh()

        # throttle the loop for performance
        time.sleep(0.2)


'''
Standard stuff, run main function if running the file
'''
if __name__ == '__main__':
    main()