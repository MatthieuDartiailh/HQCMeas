# -*- coding: utf-8 -*-

from driver_tools import (VisaInstrument, InstrIOError, instrument_property,
                          secure_communication)
from visa import VisaTypeError
from textwrap import fill
from inspect import cleandoc
import re

class AgilentPSGSignalGenerator(VisaInstrument):
    """
    """
    frequency_unit = 'GHZ'

    @instrument_property
    @secure_communication
    def fixed_frequency(self):
        freq =  self.ask_for_values(':FREQuency:FIXed?')[0]
        if freq is not None:
            return freq
        else:
            raise InstrIOError

    @fixed_frequency.setter
    @secure_communication
    def set_fixed_frequency(self, value):
        """
        """
        unit =  self.frequency_unit
        self.write(':FREQuency:FIXed {}{}'.format(value,unit))
        result = self.ask_for_values(':FREQuency:FIXed?')[0]
        if unit == 'GHZ':
            result /= 10**9
        elif unit == 'MHZ':
            result /= 10**6
        elif unit == 'KHZ':
            result /= 10**3
        if result != value:
            raise InstrIOError('Instrument did not set correctly the frequency')

    @instrument_property
    @secure_communication
    def fixed_power(self):
        power =  self.ask_for_values(':POWER?')[0]
        if power is not None:
            return power
        else:
            raise InstrIOError

    @fixed_power.setter
    @secure_communication
    def set_fixed_power(self, value):
        """
        """
        self.write(':POWER {}DBM'.format(value))
        result = self.ask_for_values('POWER?')[0]
        if result != value:
            raise InstrIOError('Instrument did not set correctly the power')

    @instrument_property
    @secure_communication
    def output(self):
        output =  self.ask_for_values(':OUTPUT?')[0]
        if output is not None:
            if output == 1:
                return True
            else:
                return False
        else:
            raise InstrIOError

    @output.setter
    @secure_communication
    def set_output(self, value):
        """
        """
        on = re.compile('on', re.IGNORECASE)
        off = re.compile('off', re.IGNORECASE)
        if on.match(value) or value == 1:
            self.write(':OUTPUT ON')
            if self.ask(':OUTPUT?')!= '1':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the output'''))
        elif off.match(value) or value == 0:
            self.write(':OUTPUT OFF')
            if self.ask(':OUTPUT?')!= '0':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the output'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                        switch_on_off method''').format(value), 80)
            raise VisaTypeError(mess)