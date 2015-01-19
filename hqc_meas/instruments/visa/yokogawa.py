# -*- coding: utf-8 -*-
#==============================================================================
# module : agilent_multimeter.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
This module defines drivers for yokogawa sources using VISA library.

:Contains:
    YokogawaGS200 : Driver for the YokogawaGS200 using VISA
    Yokogawa7651 : Driver for the Yokogawa7651 using VISA

"""
import re
from textwrap import fill
from inspect import cleandoc

from ..driver_tools import (InstrIOError, instrument_property,
                            secure_communication)
from ..visa_tools import VisaInstrument, VisaTypeError


class YokogawaGS200(VisaInstrument):
    """
    Driver for the YokogawaGS200, using the VISA library.

    This driver does not give access to all the functionnality of the
    instrument but you can extend it if needed. See the documentation of the
    `driver_tools` package for more details about writing instruments drivers.

    Parameters
    ----------
    see the `VisaInstrument` parameters in the `driver_tools` module

    Attributes
    ----------
    voltage : float, instrument_property
        Voltage at the output of the generator in volts.
    function : str, instrument_property
        Current function of the generator can be either 'VOLT' or 'CURR' (case
        insensitive).
    output : bool, instrument_property
        State of the output 'ON'(True)/'OFF'(False).

    """

    @instrument_property
    @secure_communication()
    def voltage(self):
        """Voltage getter method. NB: does not check the current function.
        """
        voltage = self.ask_for_values(":SOURce:LEVel?")[0]
        if voltage is not None:
            return voltage
        else:
            raise InstrIOError('Instrument did not return the voltage')

    @voltage.setter
    @secure_communication()
    def voltage(self, set_point):
        """Voltage setter method. NB: does not check the current function.
        """
        self.write(":SOURce:LEVel {}".format(set_point))
        value = self.ask_for_values('SOURce:LEVel?')[0]
        #to avoid floating point rouding
        if abs(value - round(set_point, 9)) > 10**-9:
            raise InstrIOError('Instrument did not set correctly the voltage')

    @instrument_property
    @secure_communication()
    def voltage_range(self):
        """ Voltage range getter method.

        NB: does not check the current function.

        """
        v_range = self.ask(":SOURce:RANGe?")
        if v_range is not None:
            if v_range == '10E-3':
                return '10 mV'
            elif v_range == '100E-3':
                return '100 mV'
            elif v_range == '1E+0':
                return '1 V'
            elif v_range == '10E+0':
                return '10 V'
            elif v_range == '30E+0':
                return '30 V'
        else:
            raise InstrIOError('Instrument did not return the range')

    @voltage_range.setter
    @secure_communication()
    def voltage_range(self, v_range):
        """Voltage range getter method.

        NB: does not check the current function.

        """
        visa_range = ''
        if v_range == '10 mV':
            visa_range = '10E-3'
        elif v_range == '100 mV':
            visa_range = '100E-3'
        elif v_range == '1 V':
            visa_range = '1E+0'
        elif v_range == '10 V':
            visa_range = '10E+0'
        elif v_range == '30 V':
            visa_range = '30E+0'

        if visa_range:
            self.write(":SOURce:RANGe {}".format(visa_range))
            check = self.ask(":SOURce:RANGe?")
            if check != visa_range:
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                    the range'''))

    @instrument_property
    @secure_communication()
    def function(self):
        """Function getter method
        """
        value = self.ask('SOURce:FUNCtion?')
        if value is not None:
            #Stripping leading and trailing '
            return value
        else:
            raise InstrIOError('Instrument did not return the function')

    @function.setter
    @secure_communication()
    def function(self, mode):
        """Function setter method
        """
        volt = re.compile('VOLT', re.IGNORECASE)
        curr = re.compile('CURR', re.IGNORECASE)
        if volt.match(mode):
            self.write(':SOURce:FUNCtion VOLT')
            value = self.ask('SOURce:FUNCtion?')
            if value[1:-1] != 'VOLT':
                raise InstrIOError('Instrument did not set correctly the mode')
        elif curr.match(mode):
            self.write(':SOURce:FUNCtion CURR')
            value = self.ask('SOURce:FUNCtion?')
            if value[1:-1] != 'CURR':
                raise InstrIOError('Instrument did not set correctly the mode')
        else:
            mess = fill('''The invalid value {} was sent to set_function
                        method of the Yokogawa driver'''.format(value), 80)
            raise VisaTypeError(mess)

    @instrument_property
    @secure_communication()
    def output(self):
        """Output getter method
        """
        value = self.ask_for_values(':OUTPUT?')
        if value is not None:
            return bool(value[0])
        else:
            raise InstrIOError('Instrument did not return the output state')

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
            mess = fill(cleandoc('''The invalid value {} was sent to set the
                    output state of the Yokogawa driver''').format(value), 80)
            raise VisaTypeError(mess)

#    def check_connection(self):
#        """Found no way to check whether or not the cache can be corrupted
#        """
#        return False


class Yokogawa7651(VisaInstrument):
    """
    Driver for the Yokogawa7651, using the VISA library.

    This driver does not give access to all the functionnality of the
    instrument but you can extend it if needed. See the documentation of the
    `driver_tools` package for more details about writing instruments drivers.

    Parameters
    ----------
    see the `VisaInstrument` parameters in the `driver_tools` module

    Attributes
    ----------
    voltage : float, instrument_property
        Voltage at the output of the generator in volts.
    function : str, instrument_property
        Current function of the generator can be either 'VOLT' or 'CURR' (case
        insensitive).
    output : bool, instrument_property
        State of the output 'ON'(True)/'OFF'(False).

    """

    @instrument_property
    @secure_communication()
    def voltage(self):
        """Voltage getter method.

        """
        data = self.ask("OD")
        voltage = float(data[4::])
        if voltage is not None:
            return voltage
        else:
            raise InstrIOError('Instrument did not return the voltage')

    @voltage.setter
    @secure_communication()
    def voltage(self, set_point):
        """Voltage setter method.

        """
        self.write("S{:+E}E".format(set_point))
        data = self.ask("OD")
        value = float(data[4::])
        #to avoid floating point rouding
        if abs(value - round(set_point, 9)) > 10**-9:
            raise InstrIOError('Instrument did not set correctly the voltage')

    @instrument_property
    @secure_communication()
    def function(self):
        """Function getter method.

        """
        data = self.ask('OD')
        if data[3] == 'V':
            return 'VOLT'
        elif data[3] == 'A':
            return 'CURR'
        else:
            raise InstrIOError('Instrument did not return the function')

    @function.setter
    @secure_communication()
    def function(self, mode):
        """Function setter method.

        """
        volt = re.compile('VOLT', re.IGNORECASE)
        curr = re.compile('CURR', re.IGNORECASE)
        if volt.match(mode):
            self.write('OS')
            self.read()
            current_range = self.read()[2:4]
            # Empty output buffer.
            self.read()
            self.read()
            self.read()
            self.write('F1{}E'.format(current_range))
            value = self.ask('OD')
            if value[3] != 'V':
                raise InstrIOError('Instrument did not set correctly the mode')
        elif curr.match(mode):
            self.write('F5E')
            value = self.ask('OD')
            if value[3] != 'A':
                raise InstrIOError('Instrument did not set correctly the mode')
        else:
            mess = fill('''The invalid value {} was sent to set_function
                        method of the Yokogawa driver'''.format(value), 80)
            raise VisaTypeError(mess)

    @instrument_property
    @secure_communication()
    def output(self):
        """Output getter method.

        """
        mess = self.ask('OC')[5::]
        value = ('{0:08b}'.format(int(mess)))[3]
        if value == '0':
            return 'OFF'
        elif value == '1':
            return 'ON'
        else:
            raise InstrIOError('Instrument did not return the output state')

    @output.setter
    @secure_communication()
    def output(self, value):
        """Output setter method.

        """
        on = re.compile('on', re.IGNORECASE)
        off = re.compile('off', re.IGNORECASE)
        if on.match(value) or value == 1:
            self.write('O1E')
            mess = self.ask('OC')[5::]  # Instr return STS1=m we want m
            if ('{0:08b}'.format(int(mess)))[3] != '1':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                            the output'''))
        elif off.match(value) or value == 0:
            self.write('O0E')
            mess = self.ask('OC')[5::]  # Instr return STS1=m we want m
            if('{0:08b}'.format(int(mess)))[3] != '0':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                            the output'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to set the
                    output state of the Yokogawa driver''').format(value), 80)
            raise VisaTypeError(mess)

    def check_connection(self):
        """
        """
        return False

DRIVERS = {'YokogawaGS200': YokogawaGS200,
           'Yokogawa7651': Yokogawa7651}
