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
            raise InstrIOError('Instrument failed to return function')
            
    @function.setter
    @secure_communication
    def function(self, value):
        self.write('FUNCtion {}'.format(value))
        if not(self.ask('FUNCtion?').lower() == value.lower()):
            raise InstrIOError('Instrument failed to set function')

    @secure_communication
    def read_voltage_dc(self, mes_range = 'DEF', mes_resolution = 'DEF'):
        """
        """
        if self.function != 'VOLT':
            self.function = 'VOLT'
        
        value = self.ask_for_values('FETCh?')
        if value:
            return value[0]
        else:
            raise InstrIOError('DC voltage measure failed')

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
            raise InstrIOError('AC voltage measure failed')

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
            raise InstrIOError('Resistance measure failed')

    @secure_communication
    def read_current_dc(self, mes_range = 'DEF', mes_resolution = 'DEF'):
        """
        """
        if self.function != 'CURR':
            self.function = 'CURR'
        
        value = self.ask_for_values('FETCh?')
        if value:
            return value[0]
        else:
            raise InstrIOError('DC current measure failed')

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
            raise InstrIOError('AC current measure failed')
    
    @secure_communication
    def check_connection(self):
        val = ('{0:08b}'.format(int(self.ask('*ESR'))))[::-1]
        if val:
            return val[6]