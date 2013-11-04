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
#import zhinst.ziPython, zhinst.utils
from math import sqrt
from .driver_tools import (BaseInstrument, InstrIOError,
                          secure_communication)

class LockInZI_HF2LI(BaseInstrument):
    """

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

    def __init__(self, connection_info, caching_allowed = True,
                 caching_permissions = {}):

        super(LockInZI_HF2LI, self).__init__(connection_info, caching_allowed,
                                                caching_permissions)
        self._device = None
        self._daq = None
        self.open_connection()

    def open_connection(self):
        """Open a connection to an instrument
        """
        # Open connection to ziServer
        self._daq = zhinst.ziPython.ziDAQServer('localhost', 8005)
        # Detect device
        self._device = zhinst.utils.autoDetect()

    def close_connection(self):
        """Close the connection established previously using `open_connection`
        """
        # Open connection to ziServer
        self._daq.close()
        # Detect device
        self._device = None

    def reopen_connection(self):
        """Reopen the connection established previously using `open_connection`
        """
        self.close_connection()
        self.reopen_connection()

    @secure_communication()
    def read_x(self):
        """
        Return the x quadrature measured by the instrument

        Perform a direct reading without any waiting. Can return non independent
        values if the instrument is queried too often.

        """
        sample = self._daq.getSample('/'+self._device+'/demods/0/sample')
        if not sample:
            raise InstrIOError('The command did not complete correctly')
        else:
            return sample['x']

    @secure_communication()
    def read_y(self):
        """
        Return the y quadrature measured by the instrument

        Perform a direct reading without any waiting. Can return non independent
        values if the instrument is queried too often.

        """
        sample = self._daq.getSample('/'+self._device+'/demods/0/sample')
        if not sample:
            raise InstrIOError('The command did not complete correctly')
        else:
            return sample['y']

    @secure_communication()
    def read_xy(self):
        """
        Return the x and y quadratures measured by the instrument

        Perform a direct reading without any waiting. Can return non independent
        values if the instrument is queried too often.

        """
        sample = self._daq.getSample('/'+self._device+'/demods/0/sample')
        if not sample:
            raise InstrIOError('The command did not complete correctly')
        else:
            return (sample['x'], sample['y'])

    @secure_communication()
    def read_amplitude(self):
        """
        Return the amplitude of the signal measured by the instrument

        Perform a direct reading without any waiting. Can return non independent
        values if the instrument is queried too often.

        """
        sample = self._daq.getSample('/'+self._device+'/demods/0/sample')
        if not sample:
            raise InstrIOError('The command did not complete correctly')
        else:
            return sqrt(sample['x']**2 + sample['x']**2)

    @secure_communication()
    def read_phase(self):
        """
        Return the phase of the signal measured by the instrument

        Perform a direct reading without any waiting. Can return non independent
        values if the instrument is queried too often.

        """
        sample = self._daq.getSample('/'+self._device+'/demods/0/sample')
        if not sample:
            raise InstrIOError('The command did not complete correctly')
        else:
            return sample['phase']

    @secure_communication()
    def read_amp_and_phase(self):
        """
        Return the amplitude and phase of the signal measured by the instrument

        Perform a direct reading without any waiting. Can return non independent
        values if the instrument is queried too often.

        """
        sample = self._daq.getSample('/'+self._device+'/demods/0/sample')
        if not sample:
            raise InstrIOError('The command did not complete correctly')
        else:
            return (sqrt(sample['x']**2 + sample['x']**2), sample['phase'])