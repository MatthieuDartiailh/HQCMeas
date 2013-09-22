# -*- coding: utf-8 -*-
"""

"""
from .driver_tools import VisaInstrument

class Agilent34410A(VisaInstrument):
    """
    """

    def read_voltage_dc(self, mes_range = 'DEF', mes_resolution = 'DEF'):
        """
        """
        instruction = "MEASure:VOLTage:DC? {},{}"
        value = self.ask_for_values(instruction.format(mes_range,
                                                       mes_resolution))[0]
        return value

    def read_voltage_ac(self, mes_range = 'DEF', mes_resolution = 'DEF'):
        """
        """
        instruction = "MEASure:VOLTage:AC? {},{}"
        value = self.ask_for_values(instruction.format(mes_range,
                                                       mes_resolution))[0]
        return value

    def read_resistance(self, mes_range = 'DEF', mes_resolution = 'DEF'):
        """
        """
        instruction = "MEASure:RESistance? {},{}"
        value = self.ask_for_values(instruction.format(mes_range,
                                                       mes_resolution))[0]
        return value

    def read_current_dc(self, mes_range = 'DEF', mes_resolution = 'DEF'):
        """
        """
        instruction = "MEASure:CURRent:DC? {},{}"
        value = self.ask_for_values(instruction.format(mes_range,
                                                       mes_resolution))[0]
        return value

    def read_current_ac(self, mes_range = 'DEF', mes_resolution = 'DEF'):
        """
        """
        instruction = "MEASure:CURRent:AC? {},{}"
        value = self.ask_for_values(instruction.format(mes_range,
                                                       mes_resolution))[0]
        return value