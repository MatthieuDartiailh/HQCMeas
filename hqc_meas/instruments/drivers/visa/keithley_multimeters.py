# =============================================================================
# module : keithley_multimeter.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
This module defines drivers for keithley multimeters using VISA library.

:Contains:
    Keithley2000 : Driver for the Keithley2000 multimeter.

"""

from ..driver_tools import (InstrIOError, secure_communication,
                            instrument_property)
from ..visa_tools import VisaInstrument


class Keithley2000(VisaInstrument):
    """Driver for Keithley 2000 using the VISA library

    This driver does not give access to all the functionnality of the
    instrument but you can extend it if needed. See the documentation of the
    driver_tools package for more details about writing instruments drivers.

    Parameters
    ----------
    see the `VisaInstrument` parameters

    Attributes
    ----------
    function : str, instrument_property
        Current function of the multimeter. Can be : 'VOLT:DC', 'VOLT:AC',
        'CURR:DC', 'CURR:AC', 'RES'. This instrument property is cached by
        default.

    Methods
    -------
    read_voltage_dc(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the DC voltage read by the instrument. Can change the function
        if needed.
    read_voltage_ac(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the AC voltage read by the instrument. Can change the function
        if needed.
    read_res(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the resistance read by the instrument. Can change the function
        if needed.
    read_current_dc(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the DC current read by the instrument. Can change the function
        if needed.
    read_current_ac(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the AC current read by the instrument. Can change the function
        if needed.

    """
    caching_permissions = {'function': True}

    protocoles = {'GPIB': 'INSTR'}

    @instrument_property
    @secure_communication()
    def function(self):
        """Function setter
        """
        value = self.ask('FUNCtion?')
        if value:
            return value
        else:
            raise InstrIOError('Keithley2000 : Failed to return function')

    @function.setter
    @secure_communication()
    def function(self, value):
        """Function setter
        """
        self.write('FUNCtion "{}"'.format(value))
        # The Keithley returns "VOLT:DC" needs to remove the quotes
        if not(self.ask('FUNCtion?')[1:-1].lower() == value.lower()):
            raise InstrIOError('Keithley2000: Failed to set function')

    @secure_communication()
    def read_voltage_dc(self, mes_range='DEF', mes_resolution='DEF'):
        """Return the DC voltage read by the instrument.

        Perform a direct reading without any waiting. Can return identical
        values if the instrument is read more often than its integration time.
        The arguments are unused and here only to make this driver and the
        agilent driver compatible.

        """
        if self.function != 'VOLT:DC':
            self.function = 'VOLT:DC'

        value = self.ask_for_values('FETCh?')
        if value:
            return value[0]
        else:
            raise InstrIOError('Keithley2000: DC voltage measure failed')

    @secure_communication()
    def read_voltage_ac(self, mes_range='DEF', mes_resolution='DEF'):
        """Return the AC voltage read by the instrument.

        Perform a direct reading without any waiting. Can return identical
        values if the instrument is read more often than its integration time.
        The arguments are unused and here only to make this driver and the
        agilent driver compatible.

        """
        if self.function != 'VOLT:AC':
            self.function = 'VOLT:AC'

        value = self.ask_for_values('FETCh?')
        if value:
            return value[0]
        else:
            raise InstrIOError('Keithley2000: AC voltage measure failed')

    @secure_communication()
    def read_resistance(self, mes_range='DEF', mes_resolution='DEF'):
        """
        Return the resistance read by the instrument.

        Perform a direct reading without any waiting. Can return identical
        values if the instrument is read more often than its integration time.
        The arguments are unused and here only to make this driver and the
        agilent driver compatible.

        """
        if self.function != 'RES':
            self.function = 'RES'

        value = self.ask_for_values('FETCh?')
        if value:
            return value[0]
        else:
            raise InstrIOError('Keithley2000: Resistance measure failed')

    @secure_communication()
    def read_current_dc(self, mes_range='DEF', mes_resolution='DEF'):
        """Return the DC current read by the instrument.

        Perform a direct reading without any waiting. Can return identical
        values if the instrument is read more often than its integration time.
        The arguments are unused and here only to make this driver and the
        agilent driver compatible.

        """
        if self.function != 'CURR:DC':
            self.function = 'CURR:DC'

        value = self.ask_for_values('FETCh?')
        if value:
            return value[0]
        else:
            raise InstrIOError('Keithley2000: DC current measure failed')

    @secure_communication()
    def read_current_ac(self, mes_range='DEF', mes_resolution='DEF'):
        """Return the AC current read by the instrument.

        Perform a direct reading without any waiting. Can return identical
        values if the instrument is read more often than its integration time.
        The arguments are unused and here only to make this driver and the
        agilent driver compatible.

        """
        if self.function != 'CURR:AC':
            self.function = 'CURR:AC'

        value = self.ask_for_values('FETCh?')
        if value:
            return value[0]
        else:
            raise InstrIOError('Keithley2000: AC current measure failed')

    @secure_communication()
    def check_connection(self):
        """Check wether or not a front panel user set the instrument in local.
        If a front panel user set the instrument in local the cache can be
        corrupted and should be cleared.

        """
        val = ('{0:08b}'.format(int(self.ask('*ESR'))))[::-1]
        if val:
            return val[6]

DRIVERS = {'Keithley2000' : Keithley2000}
