# -*- coding: utf-8 -*-

from .driver_tools import (VisaInstrument, InstrIOError, secure_communication,
                           instrument_property)

class Keithley2000(VisaInstrument):
    """
    """
    caching_permissions = {'function' : True}

    @instrument_property
    @secure_communication
    def function(self):
        """
        """
        value = self.ask('FUNCtion?')
        if value:
            return value
        else:
            raise InstrIOError('Keithley2000 : Failed to return function')

    @function.setter
    @secure_communication
    def function(self, value):
        self.write('FUNCtion "{}"'.format(value))
        # The Keithley returns "VOLT:DC" needs to remove the quotes
        if not(self.ask('FUNCtion?')[1:-1].lower() == value.lower()):
            raise InstrIOError('Keithley2000: Failed to set function')

    @secure_communication
    def read_voltage_dc(self, mes_range = 'DEF', mes_resolution = 'DEF'):
        """
        """
        if self.function != 'VOLT:DC':
            self.function = 'VOLT:DC'

        value = self.ask_for_values('FETCh?')
        if value:
            return value[0]
        else:
            raise InstrIOError('Keithley2000: DC voltage measure failed')

    @secure_communication
    def read_voltage_ac(self, mes_range = 'DEF', mes_resolution = 'DEF'):
        """
        """
        if self.function != 'VOLT:AC':
            self.function = 'VOLT:AC'

        value = self.ask_for_values('FETCh?')
        if value:
            return value[0]
        else:
            raise InstrIOError('Keithley2000: AC voltage measure failed')

    @secure_communication
    def read_resistance(self, mes_range = 'DEF', mes_resolution = 'DEF'):
        """
        """
        if self.function != 'RES':
            self.function = 'RES'

        value = self.ask_for_values('FETCh?')
        if value:
            return value[0]
        else:
            raise InstrIOError('Keithley2000: Resistance measure failed')

    @secure_communication
    def read_current_dc(self, mes_range = 'DEF', mes_resolution = 'DEF'):
        """
        """
        if self.function != 'CURR:DC':
            self.function = 'CURR:DC'

        value = self.ask_for_values('FETCh?')
        if value:
            return value[0]
        else:
            raise InstrIOError('Keithley2000: DC current measure failed')

    @secure_communication
    def read_current_ac(self, mes_range = 'DEF', mes_resolution = 'DEF'):
        """
        """
        if self.function != 'CURR:AC':
            self.function = 'CURR:AC'

        value = self.ask_for_values('FETCh?')
        if value:
            return value[0]
        else:
            raise InstrIOError('Keithley2000: AC current measure failed')

    @secure_communication
    def check_connection(self):
        val = ('{0:08b}'.format(int(self.ask('*ESR'))))[::-1]
        if val:
            return val[6]
