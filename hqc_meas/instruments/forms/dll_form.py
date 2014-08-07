# -*- coding: utf-8 -*-
# =============================================================================
# module : dll_form.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
import os
from ctypes.util import find_library
from atom.api import Unicode, Str
from .base_forms import AbstractConnectionForm

dirname = os.path.dirname
DRIVER_FOLDER = os.path.join(dirname(dirname(__file__)), 'drivers')


class DllForm(AbstractConnectionForm):
    """
    Form for instrument using a dll for communication.

    Attributes
    ----------
    lib_path : unicode
        Path to the library.

    instr_id : str
        Id used to access to the instrument using the library.

    Methods
    -------
    check()
        Check whether or not enough information have been given by the user.
        Called when the user attempt to press the ok button of the form he is
        editing.

    required_fields()
        Return a string listing the field that the user must fill. Called when
        the check method fail.
    connection_dict()

        Return a dictionnary holding all the necessary informations to open a
        connection with an instrument using the protocol for which the form was
        written. The keys msut match the ones expected by the `BaseInstrument`
        subclass which will use it.

    """

    lib_path = Unicode('')
    instr_id = Str('')

    def check(self):
        """ Check whether or not the user provided a type and an address.

        """
        path_valid = os.path.isfile(self.lib_path)
        return (path_valid and self.instr_id != '')

    def required_fields(self):
        """ Return the mandatory fields for a Dll instrument.

        """
        return 'library path and instrument id'

    def connection_dict(self):
        """ Return the connection dictionnary which will be used by the
        `DllInstrument` class to open a connection.

        """
        return {'lib_path': self.lib_path,
                'instr_id': self.instr_id}

    def _observe_driver(self, change):
        """ Keep the lib_path in sync with the selected driver.

        """
        driver = change['value']
        if hasattr(driver, 'library'):
            path = os.path.join(DRIVER_FOLDER, 'dll', driver.library)
            if os.path.isfile(path):
                self.lib_path = path
            elif find_library(driver.library):
                self.lib_path = find_library(driver.library)
            else:
                self.lib_path = ''

        else:
            self.lib_path = ''

FORMS = {'DllInstrument': DllForm}
"""Dictionnary mapping driver or driver type names to their associated form.
"""
