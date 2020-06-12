from configurable import Configurable
import requests

'''
A class for reading and managing form data, as well as submitting the data to appropriate
google forms. Inherits after configurable, but doesn't run default constructor
Details for all forms should be stored in appropriate .json files
'''
class DataSender(Configurable):

    #
    # CLASS VARIABLES
    #
    # path to form configs
    FORM_PATH = './data/json/forms'
    # names of expected forms
    FORM_CODE = ['bounty', 'loot']

    def __init__(self):
        
        #  read the forms
        self.forms = self._readForms()

    '''
    Method for submitting the data to a given form
    In: data dict, form identifier
    Out: nothing
    '''
    def submitData(self, data, form_name):

        # retrieve form URL and fields
        form_url = self.forms[form_name]['url']
        form_fld = self.forms[form_name]['fields']

        # prepare payload for the form
        form_pld = {
            'draftResponse': [],
            'pageHistory': 0
        }

        # iterate over field names and corresponding form ids in the fields dict
        for field_name, field_id in form_fld.items():

            # add an entry to payload
            form_pld[field_id] = data[field_name]

        # commit the payload and get response
        response = requests.post(form_url, data=form_pld)

        # raise an exception is bad response code
        if response.status_code != 200:
            raise requests.HTTPError(f'Invalid response code {response.status_code} when submitting {form_name}')

    '''
    Internal wrapper method for loading form data into memory
    In: none
    Out: form data dict
    '''
    def _readForms(self):

        # empty dictionary for form dicts
        form_dict = {}

        # for each form expected
        for form in self.FORM_CODE:

            # read a given form and add it ton the dict
            form_dict[form] = self.readFile(f'{self.FORM_PATH}/{form}.json')

        # return the filled dictionary
        return form_dict