# -*- coding: utf-8 -*-
"""
"""
from visa import Instrument, VisaIOError, VisaTypeError
import re
from textwrap import fill

class YokogawaGS200(Instrument):
    """
    """

    def __init__(self, connection_str):

        super(YokogawaGS200, self).__init__(connection_str)

    def set_voltage(self, set_point):
        """
        """
        self.write(":SOURce:LEVel {}".format(set_point))
        value = self.ask_for_values('SOURce:LEVel?')[0]
        if value != set_point:
            raise VisaIOError('Instrument did not set correctly the voltage')

    def get_voltage(self):
        """
        """
        return self.ask_for_values(":SOURce:LEVel?")[0]

    def set_function(self, mode):
        """
        """
        volt = re.compile('VOLT', re.IGNORECASE)
        curr = re.compile('CURR', re.IGNORECASE)
        if volt.match(mode):
            self.write(':SOURce:FUNCtion VOLT')
            value = self.ask('SOURce:FUNCtion?')
            if value != 'VOLT':
                raise VisaIOError('Instrument did not set correctly the mode')
        elif curr.match(mode):
            self.write(':SOURce:FUNCtion CURR')
            value = self.ask('SOURce:FUNCtion?')
            if value != 'CURR':
                raise VisaIOError('Instrument did not set correctly the mode')
        else:
            mess = fill('''The invalid value {} was sent to set_function
                        method of the Yokogawa driver'''.format(value), 80)
            raise VisaTypeError(mess)
            
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
                        method of the Yokogawa driver'''.format(value), 80)
            raise VisaTypeError(mess)