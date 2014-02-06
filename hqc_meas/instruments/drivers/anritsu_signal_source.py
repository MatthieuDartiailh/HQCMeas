# -*- coding: utf-8 -*-
#==============================================================================
# module : anritsu_signal_generator.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
This module defines drivers for agilent multimeters using VISA library.

:Contains:


"""

from .driver_tools import (InstrIOError, secure_communication,
                           instrument_property)
from .visa_tools import VisaInstrument

class AnritsuMG3694(VisaInstrument):
    """
    """

    def __init__(self, connection_info, caching_allowed = True,
                 caching_permissions = {}):

        self.frequency_unit = 'GHz'
        self.write("DSPL 4")
        self.write("EBW3") #'si la reference externe est très stable en phase, il faut choisir la plus grande EBW'
        self.write("LO0") #'no offset on the power
        self.write("LOG") #'Selects logarithmic power level operation in dBm
        self.write("TR1") #'Sets 40 dB of attenuation when RF is switched off
        self.write("PS1") #'Turns on the Phase Offset
        self.write("DS1") #'Turns off the secure mode
        self.write("AT1") #'Selects ALC step attenuator decoupling
        self.write("IL1") #'Selects internal leveling of output power

    @instrument_property
    @secure_communication()
    def frequency(self):
        """
        """
        freq = self.ask_for_values("OF0")
        if freq:
            if self.frequency_unit == 'GHz':
                return freq/1000
            elif self.frequency_unit == 'MHz':
                return freq
            else:
                return 0
        else:
            raise InstrIOError(''' ''')

    @frequency.setter
    @secure_communication()
    def frequency(self, value):
        """
        """
        self.write("CF0 {} {}".format(value, self.frequency_unit))

    @instrument_property
    @secure_communication()
    def power(self):
        """
        """
        power = self.ask_for_values("OF0")
        if power:
            if self.frequency_unit == 'GHz':
                return freq/1000
            elif self.frequency_unit == 'MHz':
                return freq
            else:
                return 0
        else:
            raise InstrIOError(''' ''')
            
DRIVERS = {'AnritsuMG3694' : AnritsuMG3694}