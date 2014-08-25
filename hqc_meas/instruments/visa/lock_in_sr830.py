# -*- coding: utf-8 -*-
#==============================================================================
# module : lock_in_sr830.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
This module defines a driver for the Stanford instrument lock-in SR830

:Contains:
    LockInSR830 : driver for the SR830 lock-in

"""

from ..driver_tools import (InstrIOError, secure_communication)
from ..visa_tools import VisaInstrument


class LockInSR830(VisaInstrument):
    """Driver for a SR830 lock-in, using the VISA library.

    This driver does not give access to all the functionnality of the
    instrument but you can extend it if needed. See the documentation of
    the driver_tools module for more details about writing instruments
    drivers.

    Parameters
    ----------
    see the `VisaInstrument` parameters in the `driver_tools` module

    Methods
    -------
    read_x()
        Return the x quadrature measured by the instrument
    read_y()
        Return the y quadrature measured by the instrument
    read_xy()
        Return the x and y quadratures measured by the instrument
    read_amplitude()
        Return the ammlitude of the signal measured by the instrument
    read_phase()
        Return the phase of the signal measured by the instrument
    read_amp_and_phase()
        Return the amplitude and phase of the signal measured by the instrument

    """

    def __init__(self, *args, **kwargs):

        super(LockInSR830, self).__init__(*args, **kwargs)
        bus = kwargs.get('bus', 'GPIB')
        if bus == 'GPIB':
            self.write('OUTX1')
        elif bus == 'RS232':
            self.write('OUTX0')
        else:
            raise InstrIOError('In invalib bus was specified')

    @secure_communication()
    def read_x(self):
        """
        Return the x quadrature measured by the instrument

        Perform a direct reading without any waiting. Can return non
        independent values if the instrument is queried too often.

        """
        value = self.ask_for_values('OUTP?1')
        if not value:
            raise InstrIOError('The command did not complete correctly')
        else:
            return value[0]

    @secure_communication()
    def read_y(self):
        """
        Return the y quadrature measured by the instrument

        Perform a direct reading without any waiting. Can return non
        independent values if the instrument is queried too often.

        """
        value = self.ask_for_values('OUTP?2')
        if not value:
            raise InstrIOError('The command did not complete correctly')
        else:
            return value[0]

    @secure_communication()
    def read_xy(self):
        """
        Return the x and y quadratures measured by the instrument

        Perform a direct reading without any waiting. Can return non
        independent values if the instrument is queried too often.

        """
        values = self.ask_for_values('SNAP?1,2')
        if not values:
            raise InstrIOError('The command did not complete correctly')
        else:
            return values

    @secure_communication()
    def read_amplitude(self):
        """
        Return the amplitude of the signal measured by the instrument

        Perform a direct reading without any waiting. Can return non
        independent values if the instrument is queried too often.

        """
        value = self.ask_for_values('OUTP?3')
        if not value:
            return InstrIOError('The command did not complete correctly')
        else:
            return value[0]

    @secure_communication()
    def read_phase(self):
        """
        Return the phase of the signal measured by the instrument

        Perform a direct reading without any waiting. Can return non
        independent values if the instrument is queried too often.

        """
        value = self.ask_for_values('OUTP?4')
        if not value:
            raise InstrIOError('The command did not complete correctly')
        else:
            return value[0]

    @secure_communication()
    def read_amp_and_phase(self):
        """
        Return the amplitude and phase of the signal measured by the instrument

        Perform a direct reading without any waiting. Can return non
        independent values if the instrument is queried too often.

        """
        values = self.ask_for_values('SNAP?3,4')
        if not values:
            raise InstrIOError('The command did not complete correctly')
        else:
            return values

DRIVERS = {'SR830': LockInSR830}
