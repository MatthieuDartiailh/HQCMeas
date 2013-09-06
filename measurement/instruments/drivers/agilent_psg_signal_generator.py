# -*- coding: utf-8 -*-

from visa import Instrument, VisaTypeError, VisaIOError
from textwrap import fill
import re

class AgilentPSGSignalGenerator(Instrument):
    """
    """

    def set_fixed_frequency(self, value, unit = 'GHZ'):
        """
        """
        self.write(':FREQuency:FIXed {}{}'.format(value, unit))
        result = self.ask_for_values(':FREQuency:FIXed?')[0]
        if unit == 'GHZ':
            result /= 10**9
        elif unit == 'MHZ':
            result /= 10**6
        elif unit == 'KHZ':
            result /= 10**3
        if result != value:
            raise VisaIOError('Instrument did not set correctly the frequency')

    def set_fixed_power(self, value):
        """
        """
        self.write(':POWER {}DBM'.format(value))
        result = self.ask_for_values('POWER?')[0]
        if result != value:
            raise VisaIOError('Instrument did not set correctly the power')

    def switch_on_off(self, value):
        """
        """
        on = re.compile('on', re.IGNORECASE)
        off = re.compile('off', re.IGNORECASE)
        if on.match(value):
            self.write(':OUTPUT ON')
            if self.ask(':OUTPUT?')!= '1':
                raise VisaIOError('Instrument did not set correctly the output')
        elif off.match(value):
            self.write(':OUTPUT OFF')
            if self.ask(':OUTPUT?')!= '0':
                raise VisaIOError('Instrument did not set correctly the output')
        else:
            mess = fill('''The invalid value {} was sent to switch_on_off
                        method'''.format(value), 80)
            raise VisaTypeError(mess)