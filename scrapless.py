import time
import atexit
import logging

from app import App

'''
Exit handler to clean things up
'''
def exit_handler():

    # cease all logging to prevent empty files
    logging.shutdown()

'''
Main function
'''
def main():

    # register exit handler
    atexit.register(exit_handler)

    # new instance of the main class
    scrapless = App()

    # run in try just to log 
    # unexpected exceptions
    try:

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
            time.sleep(scrapless.LOOP_INTER)

    # intercept the exception
    except Exception as e:

        # log the exception
        scrapless.logger.error(str(e))

        # shut down the app
        quit()

'''
Standard stuff, run main function if running the file
'''
if __name__ == '__main__':
    main()