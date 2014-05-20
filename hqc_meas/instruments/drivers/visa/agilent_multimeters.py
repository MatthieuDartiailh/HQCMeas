# -*- coding: utf-8 -*-
#==============================================================================
# module : agilent_multimeter.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
This module defines drivers for agilent multimeters using VISA library.

:Contains:
    Agilent34410A

"""

from ..driver_tools import (InstrIOError, secure_communication)
from ..visa_tools import VisaInstrument


class Agilent34410A(VisaInstrument):
    """
    Driver for an Agilent 34410A multimeter, using the VISA library.

    This driver does not give access to all the functionnality of the
    instrument but you can extend it if needed. See the documentation of
    the `driver_tools` module for more details about writing instruments
    drivers.

    Parameters
    ----------
    see the `VisaInstrument` parameters in the `driver_tools` module

    Methods
    -------
    read_voltage_dc(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the DC voltage measured by the instrument
    read_voltage_ac(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the AC voltage measured by the instrument
    read_resistance(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the resistance measured by the instrument
    read_current_dc(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the DC current measured by the instrument
    read_current_ac(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the AC current measured by the instrument

    Notes
    -----
    This driver has been written for the Agilent 34410A but might work for
    other models using the same SCPI commands.

    """
    @secure_communication()
    def read_voltage_dc(self, mes_range='DEF', mes_resolution='DEF'):
        """Return the DC voltage measured by the instrument
        """
        instruction = "MEASure:VOLTage:DC? {},{}"
        value = self.ask_for_values(instruction.format(mes_range,
                                                       mes_resolution))
        if value:
            return value[0]
        else:
            raise InstrIOError('DC voltage measure failed')

    @secure_communication()
    def read_voltage_ac(self, mes_range='DEF', mes_resolution='DEF'):
        """Return the AC voltage measured by the instrument
        """
        instruction = "MEASure:VOLTage:AC? {},{}"
        value = self.ask_for_values(instruction.format(mes_range,
                                                       mes_resolution))
        if value:
            return value[0]
        else:
            raise InstrIOError('AC voltage measure failed')

    @secure_communication()
    def read_resistance(self, mes_range='DEF', mes_resolution='DEF'):
        """Return the resistance measured by the instrument
        """
        instruction = "MEASure:RESistance? {},{}"
        value = self.ask_for_values(instruction.format(mes_range,
                                                       mes_resolution))
        if value:
            return value[0]
        else:
            raise InstrIOError('Resistance measure failed')

    @secure_communication()
    def read_current_dc(self, mes_range='DEF', mes_resolution='DEF'):
        """Return the DC current measured by the instrument
        """
        instruction = "MEASure:CURRent:DC? {},{}"
        value = self.ask_for_values(instruction.format(mes_range,
                                                       mes_resolution))
        if value:
            return value[0]
        else:
            raise InstrIOError('DC current measure failed')

    @secure_communication()
    def read_current_ac(self, mes_range='DEF', mes_resolution='DEF'):
        """Return the AC current measured by the instrument
        """
        instruction = "MEASure:CURRent:AC? {},{}"
        value = self.ask_for_values(instruction.format(mes_range,
                                                       mes_resolution))
        if value:
            return value[0]
        else:
            raise InstrIOError('AC current measure failed')

DRIVERS = {'Agilent34410A': Agilent34410A}
