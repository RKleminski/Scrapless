import pytesseract
import pyautogui

from settings import AppSettings


'''
Primary application class, with all necessary components
stored as instance variables, initialised on startup
This is the heart of the application
'''
class App:

    def __init__(self):

        # initialise settings
        self.app_settings = AppSettings()

        # initialise overlay
        self.overlay = self.app_settings.configureOverlay()

        # initialise screen capture as empty
        self.screen_capture = None

        # point pytesseract at tesseract installation
        self.setPyTesseract()

    '''
    Configure pytesseract using read path
    '''
    def setPyTesseract(self):

        # use the path read from config to setup pytesseract
        pytesseract.pytesseract.tesseract_cmd = self.app_settings.tesseract_path

    '''
    Capture new screenshot and store it within
    the instance of this class
    '''
    def screenCap(self):

        self.screen_capture = pyautogui.screenshot(region=(0, 0, 1920, 1080))

    '''
    Method for printing out an output to logs and to overlay
    This is a convenience function to reduce clutter and keep 
    user information level high
    '''
    def writeOutput(self, text, colour):

        # only call the overlay method if said overlay is enabled
        if self.overlay:
            self.overlay.writeLine(text.replace('\n', ''), colour)

        # write out to log
        self.app_settings.logger.info(text)