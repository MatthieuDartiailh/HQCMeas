# -*- coding: utf-8 -*-
#==============================================================================
# module : AWG.py
# author : Pierre Heidmann
# license : MIT license
#==============================================================================
"""

This module defines drivers for LabBrick using DLL Library.

:Contains:
    LabBrickDll
    LabBrickLMS103


To read well the Dll of the LabBrick, Visual C++ Studio 2013 is needed.

"""
from ..driver_tools import (InstrIOError, secure_communication,
                            instrument_property)
from ..dll_tools import DllLibrary, DllInstrument
from inspect import cleandoc
import ctypes


class LabBrickDll(DllLibrary):
    """ Wrapper for the Labbrick dll library (vnx_fmsynth.dll).

    """
    def __init__(self, path, **kwargs):

        super(LabBrickDll, self).__init__(path, **kwargs)

        # dict {serial_num: ids}
        self.devIDs = {}
        self.initialized_devices = []

# See what we have connected
        self.connected_instruments()

    def connected_instruments(self):
        """ Return the serial number of each connected instruments.

        """
        numDevices = self.dll.fnLMS_GetNumDevices()
        devIDsArray = numDevices*ctypes.c_uint
        devIDs = devIDsArray()
        self.dll.fnLMS_GetDevInfo(ctypes.byref(devIDs))
        for tmpID in devIDs:
            tmpNum = self.dll.fnLMS_GetSerialNumber(tmpID)
            self.devIDs[tmpNum] = tmpID

        return self.devIDs.keys()

    def id_from_serial_number(self, serial_number):
        """ Return the ID from the serial_number of a connected instrument.

        """
        if serial_number in self.devIDs.keys():
            return self.devIDs[serial_number]
        else:
            raise ValueError(cleandoc('''Instrument {} is not connected'''
                                      .format(serial_number)))

    def connect(self, devID):
        """ Connect LabBrick instrument of ID devID

        """

        if devID in self.devIDs.values():
            status = self.dll.fnLMS_InitDevice(devID)
            if status != 0:
                mes = 'Unable to connect to Labbrick {}.'.format(devID)
                return InstrIOError(mes)
        else:
            raise ValueError(cleandoc('''Instrument {} is not connected'''
                                      .format(devID)))

    def disconnect(self, devID):
        """

        """
# Close device if open
        if self.open(devID):
            self.dll.fnLMS_CloseDevice(devID)
        else:
            raise ValueError(cleandoc('''Instrument {} is not connected'''
                                      .format(devID)))

    def set_test_mode(self, value):
        ''' Activate/desactivate test mode.

        Parameters
        ----------
        value : bool
            If True activates the test in which two instruments are considered
            connected : one LMS-103, one LMS-123

        '''
        if value in ('True', 'Yes', 1):
            self.dll.fnLMS_SetTestMode(1)
        elif value in ('False', 'No', 0):
            self.dll.fnLMS_SetTestMode(0)
        else:
            raise ValueError(cleandoc('''{} is an invalid value'''
                                      .format(value)))

# Some properties of the device
    def open(self, devID):
        statusBits = self.dll.fnLMS_GetDeviceStatus(devID)
        if statusBits < 2:
            return False
        else:
            return bin(statusBits)[-2] == '1'

    def get_frequency(self, devID):
        return self.dll.fnLMS_GetFrequency(devID)

    def set_frequency(self, value, devID):
        self.dll.fnLMS_SetFrequency(devID, value)

    def get_power(self, devID):
        return self.dll.fnLMS_GetPowerLevel(devID)

    def set_power(self, value, devID):
        self.dll.fnLMS_SetPowerLevel(devID, value)

    def get_freqref(self, devID):
        return self.dll.fnLMS_GetUseInternalRef(devID)

    def set_freqref(self, value, boolean, devID):
        try:
            self.dll.fnLMS_SetUseInternalRef(devID, boolean)
        except KeyError:
            self.dll.fnLMS_SetUseInternalRef(devID, value)

    def get_output(self, devID):
        return self.dll.fnLMS_GetRF_On(devID)

    def set_output(self, value, devID):
        self.dll.fnLMS_SetRFOn(devID, value)

    def get_extpulsemod(self, devID):
        return self.dll.fnLMS_GetUseInternalPulseMod(devID)

    def set_extpulsemod(self, value, devID):
        self.dll.fnLMS_SetUseExternalPulseMod(devID, value)

    def get_maxpower(self, devID):
        return self.dll.fnLMS_GetMaxPwr(devID)

    def get_minpower(self, devID):
        return self.dll.fnLMS_GetMinPwr(devID)

    def get_maxfreq(self, devID):
        return self.dll.fnLMS_GetMaxFreq(devID)

    def get_minfreq(self, devID):
        return self.dll.fnLMS_GetMinFreq(devID)

    def plllocked(self, devID):
        return self.dll.fnLMS_GetDeviceStatus(devID)


class LabBrickLMS103(DllInstrument):

    library = 'vnx_fmsynth.dll'

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        super(LabBrickLMS103, self).__init__(connection_info, caching_allowed,
                                             caching_permissions, auto_open)

        self._dll = LabBrickDll(connection_info['lib_path'])

# load the ID of the device from the serial number
        serial = int(connection_info['instr_id'])
        self.devID = self._dll.id_from_serial_number(serial)
        self.serial = serial

        if auto_open:
            self.open_connection()
            # load some useful properties of the device
            self.maxPower = self.max_power
            self.minPower = self.min_power
            self.maxFreq = self.max_freq
            self.minFreq = self.min_freq

    def open_connection(self):
        """ Open a connection to the instrument.

        """
        self._dll.connect(self.devID)

    def close_connection(self):
        """ Close the connection established previously using `open_connection`

        """
        self._dll.disconnect(self.devID)

    def reopen_connection(self):
        """ Reopen connection established previously using `open_connection`

        """
        if self._dll.open(self.devID):
            mes = 'Instrument {} is already opened'.format(self.serial)
            raise InstrIOError(mes)
        else:
            self._dll.connect(self.devID)

    def connected(self):
        """ Check whether or not the instrument is connected

        """
        self._dll.open(self.devID)

    @instrument_property
    @secure_communication()
    def max_power(self):
        with self._dll.secure():
            if self.devID is not None:
                maxpower = self._dll.get_maxpower(self.devID)/4
                if maxpower is not None:
                    return maxpower
                else:
                    raise InstrIOError
            else:
                return InstrIOError

    @instrument_property
    @secure_communication()
    def min_power(self):
        with self._dll.secure():
            if self.devID is not None:
                minpower = self._dll.get_minpower(self.devID)/4
                if minpower is not None:
                    return minpower
                else:
                    raise InstrIOError
            else:
                return InstrIOError

    @instrument_property
    @secure_communication()
    def max_freq(self):
        with self._dll.secure():
            if self.devID is not None:
                maxfreq = self._dll.get_maxfreq(self.devID)/1e8
                if maxfreq is not None:
                    return maxfreq
                else:
                    raise InstrIOError
            else:
                return InstrIOError

    @instrument_property
    @secure_communication()
    def min_freq(self):
        with self._dll.secure():
            if self.devID is not None:
                minfreq = self._dll.get_minfreq(self.devID)/1e8
                if minfreq is not None:
                    return minfreq
                else:
                    raise InstrIOError
            else:
                return InstrIOError

    @instrument_property
    @secure_communication()
    def frequency(self):
        ''' frequency getter method.

        '''
        with self._dll.secure():
            if self.devID is not None:
                freq = self._dll.get_frequency(self.devID)/1e8
                if freq is not None:
                    return freq
                else:
                    raise InstrIOError
            else:
                return InstrIOError

    @frequency.setter
    @secure_communication()
    def frequency(self, value):
        """ Frequency setter method.

        Input : float, No string

        """
        with self._dll.secure():
            if self.devID is not None:
                if (value <= self.maxFreq) and (value >= self.minFreq):
                    self._dll.set_frequency(int(value*1e8), self.devID)
                else:
                    mes = cleandoc('''The frequency asked for is outside of the
                                   LabBricks range: {0} to {1}'''
                                   .format(self.minFreq, self.maxFreq))
                    raise InstrIOError(mes)
                result = self._dll.get_frequency(self.devID)
                if abs(result - int(value*1e8)) > 10**-12:
                    mes = 'Instrument did not set correctly the frequency'
                    raise InstrIOError(mes)
            else:
                raise InstrIOError

    @instrument_property
    @secure_communication()
    def power(self):
        ''' power getter method.

        '''
        with self._dll.secure():
            if self.devID is not None:
                power = self.maxPower - self._dll.get_power(self.devID)*0.25
                if power is not None:
                    return power
                else:
                    raise InstrIOError
            else:
                return InstrIOError

    @power.setter
    @secure_communication()
    def power(self, value):
        ''' power setter method.
        Input : number, No string

        '''
        with self._dll.secure():
            if self.devID is not None:
                if (value <= self.maxPower) and (value >= self.minPower):
                    self._dll.set_power(int(value*4), self.devID)
                else:
                    mes = cleandoc('''The power asked for is outside of the
                                   LabBricks range: {0} to {1}.'''
                                   .format(self.minPower, self.maxPower))
                    raise InstrIOError(mes)
                result = self.maxPower*4 - self._dll.get_power(self.devID)
                if abs(result - int(value*4)) > 10**-12:
                    mes = 'Instrument did not set correctly the power'
                    raise InstrIOError(mes)
            else:
                raise InstrIOError

    @instrument_property
    @secure_communication()
    def freqref(self):
        ''' Reference frequency getter method.
        Input = None
        Output = {'0' = external mode, '1e-8' = internal mode}

        '''
        with self._dll.secure():
            if self.devID is not None:
                freqref = self._dll.get_freqref(self.devID)/1e8
                if freqref is not None:
                    return freqref
                else:
                    raise InstrIOError
            else:
                return InstrIOError

    @freqref.setter
    @secure_communication()
    def freqref(self, freqref):
        ''' Reference frequency setter method.
        Input = {'int', 'internal', 'ext', 'external'}
        Output = None

        '''
        with self._dll.secure():
            str2boolMap = {'int': True, 'internal': True, 'ext': False,
                           'external': False}
            if self.devID is not None:
                self._dll.set_freqref(freqref, str2boolMap[freqref],
                                      self.devID)
            else:
                return InstrIOError

    @instrument_property
    @secure_communication()
    def output(self):
        ''' Output getter method.
        Input = None
        Output = {'1' = on, '0' = off}

        '''
        with self._dll.secure():
            if self.devID is not None:
                output = self._dll.get_output(self.devID)
                if output is not None:
                    return output
                else:
                    raise InstrIOError
            else:
                return InstrIOError

    @output.setter
    @secure_communication()
    def output(self, value):
        ''' Output setter method.
        Input = {1 = on, 0 = off} (careful: No string)
        Output = None

        '''
        with self._dll.secure():
            if self.devID is not None:
                self._dll.set_output(value, self.devID)
                result = self._dll.get_output(self.devID)
                if abs(result - value) > 10**-12:
                    mes = 'Instrument did not set correctly the output'
                    raise InstrIOError(mes)
            else:
                raise InstrIOError

    @instrument_property
    @secure_communication()
    def extpulsemod(self):
        ''' external Pulse mode getter method.
        Input = None
        Output = {True, False}

        '''
        with self._dll.secure():
            if self.devID is not None:
                return self._dll.get_extpulsemod(self.devID) == 0
            else:
                return InstrIOError

    @extpulsemod.setter
    @secure_communication()
    def extpulsemod(self, value):
        ''' external Pulse mode getter method.
        Input = {True, False, 1, 0} (careful: No string)
        Output = None

        '''
        with self._dll.secure():
            if self.devID is not None:
                self._dll.set_extpulsemod(value, self.devID)
            else:
                return InstrIOError

    @instrument_property
    @secure_communication()
    def plllocked(self):
        with self._dll.secure():
            if self.devID is not None:
                statusBits = self._dll.plllocked(self.devID)
                if statusBits < 64:
                    return False
                else:
                    return bin(statusBits)[-7] == '1'
            else:
                return InstrIOError

DRIVERS = {'LabBrickLMS103': LabBrickLMS103}
