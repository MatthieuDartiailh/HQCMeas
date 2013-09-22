# -*- coding: utf-8 -*-
"""
"""
from driver_tools import (VisaInstrument, InstrIOError, instrument_property,
                          secure_communication)
import re
from visa import VisaTypeError
from textwrap import fill
from inspect import cleandoc

class YokogawaGS200(VisaInstrument):
    """
    """

    @instrument_property
    @secure_communication
    def voltage(self):
        """
        """
        voltage = self.ask_for_values(":SOURce:LEVel?")[0]
        if voltage is not None:
            return voltage
        else:
            raise InstrIOError('Instrument did not return the voltage')

    @voltage.setter
    @secure_communication
    def set_voltage(self, set_point):
        """
        """
        self.write(":SOURce:LEVel {}".format(set_point))
        value = self.ask_for_values('SOURce:LEVel?')[0]
        if value != set_point:
            raise InstrIOError('Instrument did not set correctly the voltage')

    @instrument_property
    @secure_communication
    def function(self):
        """
        """
        value = self.ask('SOURce:FUNCtion?')
        if value is not None:
            return value
        else:
            raise InstrIOError('Instrument did not return the function')

    @function.setter
    @secure_communication
    def set_function(self, mode):
        """
        """
        volt = re.compile('VOLT', re.IGNORECASE)
        curr = re.compile('CURR', re.IGNORECASE)
        if volt.match(mode):
            self.write(':SOURce:FUNCtion VOLT')
            value = self.ask('SOURce:FUNCtion?')
            if value != 'VOLT':
                raise InstrIOError('Instrument did not set correctly the mode')
        elif curr.match(mode):
            self.write(':SOURce:FUNCtion CURR')
            value = self.ask('SOURce:FUNCtion?')
            if value != 'CURR':
                raise InstrIOError('Instrument did not set correctly the mode')
        else:
            mess = fill('''The invalid value {} was sent to set_function
                        method of the Yokogawa driver'''.format(value), 80)
            raise VisaTypeError(mess)

    @instrument_property
    @secure_communication
    def output(self):
        """
        """
        value = self.ask(':OUTPUT?')
        if value is not None:
            return value
        else:
            raise InstrIOError('Instrument did not return the output state')

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
        elif off.match(value) or value ==0:
            self.write(':OUTPUT OFF')
            if self.ask(':OUTPUT?')!= '0':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                            the output'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to set the
                    output state of the Yokogawa driver''').format(value), 80)
            raise VisaTypeError(mess)