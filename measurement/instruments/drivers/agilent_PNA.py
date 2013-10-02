# -*- coding: utf-8 -*-
#==============================================================================
# module : agilent_pna.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
This module defines drivers for agilent multimeters using VISA library.

:Contains:
    Agilent34410A

"""
from inspect import cleandoc
from .driver_tools import (VisaInstrument, InstrIOError, secure_communication,
                           instrument_property)

class AgilentPNA(VisaInstrument):
    """
    """
    current_channel = 1
    current_port = 1

    @instrument_property
    @secure_communication
    def frequency(self):
        """Frequency getter method
        """
        freq =  self.ask_for_values('SENS{}:FREQuency:CENTer?'.format(
                                                    self.current_channel))
        if freq:
            return freq[0]
        else:
            raise InstrIOError(cleandoc('''Agilent PNA did not return the
                    channel {} frequency'''.format(self.current_channel)))

    @frequency.setter
    @secure_communication
    def frequency(self, value):
        """Frequency setter method
        """
        self.write('SENS{}:FREQuency:CENTer {}'.format(self.current_channel,
                                                       value))
        result = self.ask_for_values('SENS{}:FREQuency:CENTer?'.format(
                                                    self.current_channel))
        if result:
            if abs(result[0] - value) > 10**-12:
                raise InstrIOError(cleandoc('''PNA did not set correctly the
                    channel {} frequency'''.format(self.current_channel)))
        else:
            raise InstrIOError(cleandoc('''PNA did not set correctly the
                    channel {} frequency'''.format(self.current_channel)))

    @instrument_property
    @secure_communication
    def power(self):
        """Power getter method
        """
        power =  self.ask_for_values('SOUR{}:POWer{}:AMPL?'.format(
                                        self.current_channel,
                                        self.current_port))
        if power:
            return power[0]
        else:
            raise InstrIOError

    @power.setter
    @secure_communication
    def power(self, value):
        """Power setter method
        """
        self.write('SOUR{}:POWer{}:AMPL {}'.format(self.current_channel,
                                                   self.current_port,
                                                   value))
        result =  self.ask_for_values('SOUR{}:POWer{}:AMPL?'.format(
                                        self.current_channel,
                                        self.current_port))
        if result:
            if abs(result[0] > value) > 10**-12:
                raise InstrIOError('PNA did not set correctly the power')

    def read_formatted_data(self, channel = None, meas_name = ''):
        """
        """
        pass

    #getter
    def selected_measure(self):
        pass

    #setter
    def selected_measure(self):
        pass

    def get_defined_channels(self):
        """
        """
        pass

    def create_channel(self, channel_num):
        pass

    def create_meas(self, meas_name):
        pass

    def delete_meas(self, meas_name):
        pass

    def trigger_mode(self):
        pass

    def trigger_mode(self, value):
        pass

    def if_band_width(self):
        pass

    def if_band_width(self, value):
        pass