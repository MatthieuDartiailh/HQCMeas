# -*- coding: utf-8 -*-
#==============================================================================
# module : agilent_multimeter.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
This module defines drivers for agilent PSG SignalGenerator using VISA library.

:Contains:
    AgilentPSGSignalGenerator : tested for Agilent

"""

from ..driver_tools import (InstrIOError, instrument_property,
                            secure_communication)
from ..visa_tools import VisaInstrument
from visa import VisaTypeError
from textwrap import fill
from inspect import cleandoc
import re


class AgilentPSGSignalGenerator(VisaInstrument):
    """
    Generic driver for Agilent PSG SignalGenerator, using the VISA library.

    This driver does not give access to all the functionnality of the
    instrument but you can extend it if needed. See the documentation of
    the driver_tools module for more details about writing instruments
    drivers.

    Parameters
    ----------
    see the `VisaInstrument` parameters

    Attributes
    ----------
    frequency_unit : str
        Frequency unit used by the driver. The default unit is 'GHz'. Other
        valid units are : 'MHz', 'KHz', 'Hz'
    frequency : float, instrument_property
        Fixed frequency of the output signal.
    power : float, instrument_property
        Fixed power of the output signal.
    output : bool, instrument_property
        State of the output 'ON'(True)/'OFF'(False).

    Notes
    -----
    This driver has been written for the  but might work for other
    models using the same SCPI commands.

    """
    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        super(AgilentPSGSignalGenerator, self).__init__(connection_info,
                                                        caching_allowed,
                                                        caching_permissions,
                                                        auto_open)
        self.frequency_unit = 'GHz'

    @instrument_property
    @secure_communication()
    def frequency(self):
        """Frequency getter method
        """
        freq = self.ask_for_values(':FREQuency:FIXed?')
        if freq:
            return freq[0]
        else:
            raise InstrIOError

    @frequency.setter
    @secure_communication()
    def frequency(self, value):
        """Frequency setter method
        """
        unit = self.frequency_unit
        self.write(':FREQuency:FIXed {}{}'.format(value, unit))
        result = self.ask_for_values(':FREQuency:FIXed?')
        if result:
            if unit == 'GHz':
                result[0] /= 10**9
            elif unit == 'MHz':
                result[0] /= 10**6
            elif unit == 'KHz':
                result[0] /= 10**3
            if abs(result[0] - value) > 10**-12:
                mes = 'Instrument did not set correctly the frequency'
                raise InstrIOError(mes)

    @instrument_property
    @secure_communication()
    def power(self):
        """Power getter method
        """
        power = self.ask_for_values(':POWER?')[0]
        if power is not None:
            return power
        else:
            raise InstrIOError

    @power.setter
    @secure_communication()
    def power(self, value):
        """Power setter method
        """
        self.write(':POWER {}DBM'.format(value))
        result = self.ask_for_values('POWER?')[0]
        if abs(result - value) > 10**-12:
            raise InstrIOError('Instrument did not set correctly the power')

    @instrument_property
    @secure_communication()
    def output(self):
        """Output getter method
        """
        output = self.ask_for_values(':OUTPUT?')
        if output is not None:
            return bool(output[0])
        else:
            mes = 'PSG signal generator did not return its output'
            raise InstrIOError(mes)

    @output.setter
    @secure_communication()
    def output(self, value):
        """Output setter method
        """
        on = re.compile('on', re.IGNORECASE)
        off = re.compile('off', re.IGNORECASE)
        if on.match(value) or value == 1:
            self.write(':OUTPUT ON')
            if self.ask(':OUTPUT?') != '1':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the output'''))
        elif off.match(value) or value == 0:
            self.write(':OUTPUT OFF')
            if self.ask(':OUTPUT?') != '0':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the output'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                        switch_on_off method''').format(value), 80)
            raise VisaTypeError(mess)

DRIVERS = {'AgilentE8257D': AgilentPSGSignalGenerator}
