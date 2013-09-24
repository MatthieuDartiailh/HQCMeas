# -*- coding: utf-8 -*-
"""

"""
# -*- coding: utf-8 -*-

from .driver_tools import (VisaInstrument, InstrIOError, secure_communication)

class Agilent34410A(VisaInstrument):
    """
    """
    @secure_communication
    def read_voltage_dc(self, mes_range = 'DEF', mes_resolution = 'DEF'):
        """
        """
        instruction = "MEASure:VOLTage:DC? {},{}"
        value = self.ask_for_values(instruction.format(mes_range,
                                                       mes_resolution))
        if value:
            return value[0]
        else:
            raise InstrIOError('DC voltage measure failed')

    @secure_communication
    def read_voltage_ac(self, mes_range = 'DEF', mes_resolution = 'DEF'):
        """
        """
        instruction = "MEASure:VOLTage:AC? {},{}"
        value = self.ask_for_values(instruction.format(mes_range,
                                                       mes_resolution))
        if value:
            return value[0]
        else:
            raise InstrIOError('AC voltage measure failed')

    @secure_communication
    def read_resistance(self, mes_range = 'DEF', mes_resolution = 'DEF'):
        """
        """
        instruction = "MEASure:RESistance? {},{}"
        value = self.ask_for_values(instruction.format(mes_range,
                                                       mes_resolution))
        if value:
            return value[0]
        else:
            raise InstrIOError('Resistance measure failed')

    @secure_communication
    def read_current_dc(self, mes_range = 'DEF', mes_resolution = 'DEF'):
        """
        """
        instruction = "MEASure:CURRent:DC? {},{}"
        value = self.ask_for_values(instruction.format(mes_range,
                                                       mes_resolution))
        if value:
            return value[0]
        else:
            raise InstrIOError('DC current measure failed')

    @secure_communication
    def read_current_ac(self, mes_range = 'DEF', mes_resolution = 'DEF'):
        """
        """
        instruction = "MEASure:CURRent:AC? {},{}"
        value = self.ask_for_values(instruction.format(mes_range,
                                                       mes_resolution))
        if value:
            return value[0]
        else:
            raise InstrIOError('AC current measure failed')