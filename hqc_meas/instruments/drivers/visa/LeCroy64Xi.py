# -*- coding: utf-8 -*-
#==============================================================================
# module : LeCroy64Xi.py
# author : Pierre Heidmann
# license : MIT license
#==============================================================================
"""
This module defines drivers for LeCroy64Xi using VISA library.

:Contains:
    LeCroy64Xi


 LeCroy_354Xi.py class,
 to perform the communication between the Wrapper and the device


 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

"""
from threading import Lock
from contextlib import contextmanager
from ..driver_tools import (BaseInstrument, InstrIOError, secure_communication,
                            instrument_property)
from ..visa_tools import VisaInstrument
from inspect import cleandoc
import time


class LeCroyChannel(BaseInstrument):

    def __init__(self, LeCroy64Xi, channel_num, caching_allowed=True,
                 caching_permissions={}):
        super(LeCroyChannel, self).__init__(None, caching_allowed,
                                            caching_permissions)
        self._LeCroy64Xi = LeCroy64Xi
        self._channel = channel_num

    @contextmanager
    def secure(self):
        i = 0
        while not self._LeCroy64Xi.lock.acquire():
            time.sleep(0.1)
            i += 1
            if i > 50:
                raise InstrIOError
        try:
            yield
        finally:
            self._LeCroy64Xi.lock.release()

    @instrument_property
    @secure_communication()
    def verticalbase(self):
        ''' Get vertical sensitivity in Volts/div of the channel

        Input:
        None

        Output:
        value (str) : Vertical base in V.
        '''
        with self.secure():
            result = self._LeCroy64Xi.ask('C{}:VDIV?'.format(self._channel))
            result = result.replace('C{}:VDIV '.format(self._channel), '')
            return result

    @verticalbase.setter
    @secure_communication()
    def verticalbase(self, value):
        ''' Set vertical sensitivity in Volts/div of the channel

        Input:
        value (str) : Vertical base in V. (UV (microvolts), MV (milivolts),
        V (volts) or KV (kilovolts))
        (Example: '20E-3', '20 MV')

        Output:
        None
        '''
        with self.secure():
            self._LeCroy64Xi.write('C{}:VDIV {}'.format(self._channel, value))
            result = self._LeCroy64Xi.ask('C{}:VDIV?'.format(self._channel))
            result = result.replace('C{}:VDIV '.format(self._channel), '')
            result = result.replace('V', '')
            result = float(result)
            if value[-2:] == ' V':
                value_expected = float(value[:-2])
            elif value[-2:] == 'UV':
                value_expected = float(value[:-3])*1e-6
            elif value[-2:] == 'MV':
                value_expected = float(value[:-3])*1e-3
            elif value[-2:] == 'KV':
                value_expected = float(value[:-3])*1e3
            else:
                value_expected = float(value)
            if result != value_expected:
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                            the verticalbase'''))

    @secure_communication()
    def do_save_data(self):
        ''' Store a trace in ASCII format in internal memory

        Input:
        channel(int) : channel

        Output:
        None
        '''
        with self.secure():
            self._LeCroy64Xi.write('STST C{},HDD,AUTO,OFF,FORMAT,ASCII; STO'
                                   .format(self._channel))

    @secure_communication()
    def add_save_data_func(self):
        ''' Adds save_ch[n]_data functions, based on _do_save_data(channel).
        n = (1,2,3,4) for 4 channels.

        '''
        with self.secure():
            func = lambda: self.do_save_data(self._channel)
            setattr(self, 'save_ch{}_data'.format(self._channel), func)


class LeCroy64Xi(VisaInstrument):
    ''' This is the python driver for the LeCroy Waverunner 44Xi
    Digital Oscilloscope

    Usage:
    Initialize with
    <name>= instruments.create('name', 'LeCroy_44Xi', address='<VICP address>')
    <VICP address> = VICP::<ip-address>
    '''
    caching_permissions = {'defined_channels': True}

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super(LeCroy64Xi, self).__init__(connection_info,
                                         caching_allowed,
                                         caching_permissions,
                                         auto_open)

        ''' Initializes the LeCroy 44Xi.

        Input:
        None

        Output:
        None
        '''
#        self._values = {}
#        self.unitoftime = 'S'
#
#        # Make Load/Delete Waveform functions for each channel
#        for ch in range(1, 5):
#            self._add_save_data_func(ch)
#
#        self.get_all()

        self.channels = {}
        self.lock = Lock()

    def get_channel(self, num):
        """
        """
        if num not in self.defined_channels:
            return None

        if num in self.channels:
            return self.channels[num]
        else:
            channel = LeCroyChannel(self, num)
            self.channels[num] = channel
            return channel

    @instrument_property
    @secure_communication()
    def defined_channels(self):
        """
        """
        defined_channels = ['1', '2', '3', '4']
        return defined_channels

    @instrument_property
    @secure_communication()
    def trigger_mode(self):
        ''' Method to get the trigger mode

        '''
        mode = self.ask('TRMD?')
        if mode is not None:
            mode = mode.replace('TRMD ', '')
            return mode
        else:
            mes = 'LeCroy 354A did not return its trigger mode'
            raise InstrIOError(mes)

    @trigger_mode.setter
    @secure_communication()
    def trigger_mode(self, value):
        ''' Method to set the trigger mode

        Input:
        {'AUTO','NORM','SINGLE','STOP'}
        '''
        self.write('TRMD {}'.format(value))
        result = self.ask('TRMD?')
        result = result.replace('TRMD ', '')
        if result != value:
            raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the trigger mode'''))

    @secure_communication()
    def auto_setup(self):
        ''' Adjust vertical, timebase and trigger parameters automatically

        Input:
        None

        Output:
        None
        '''
        self.write('ASET')

    @instrument_property
    @secure_communication()
    def timebase(self):
        ''' Method to get the time base.

        Input:
        None

        Output:
        value (str) : Timebase in S
        '''
        result = self.ask('TDIV?')
        result = result.replace('TDIV ', '')
        if result is not None:
            return result
        else:
            mes = 'LeCroy 354A did not return its timebase'
            raise InstrIOError(mes)

    @timebase.setter
    @secure_communication()
    def timebase(self, value):
        ''' Modify the timebase setting

        Input:
        value (str): Timebase in S. (NS (nanosec), US (microsec), MS (milisec),
        S (sec) or KS (kilosec))
        (Example: '50E-6', '50 MS')

        Output:
        None
        '''

        self.write('TDIV {}'.format(value))
        result = self.ask('TDIV?')
        result = result.replace('TDIV ', '')
        result = result.replace('S', '')
        result = float(result)
        if value[-2:] == ' S':
            value_expected = float(value[:-2])
        elif value[-2:] == 'US':
            value_expected = float(value[:-3])*1e-6
        elif value[-2:] == 'MS':
            value_expected = float(value[:-3])*1e-3
        elif value[-2:] == 'KS':
            value_expected = float(value[:-3])*1e3
        else:
            value_expected = float(value)
        if result != value_expected:
            raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the timebase'''))

    @instrument_property
    @secure_communication()
    def memory_size(self):
        ''' Get the current maximum memory length used to capture waveforms.
        Input:
        None
        Output:
        result(float) : maximum memory size in Samples
        '''

        result = self.ask('MSIZ?')
        result = result.replace('MSIZ ', '')
        result = result.replace(' SAMPLE', '')
        return float(result)

    @memory_size.setter
    @secure_communication()
    def memory_size(self, msize):
        ''' Set the current maximum memory length used to capture waveforms.
        Input:
        msize(float) : Max. memory length size in Samples.
        Output:
        None
        '''
        self.write('MSIZ {}'.format(msize))
        result = self.ask('MSIZ?')
        result = result.replace('MSIZ ', '')
        result = float(result.replace(' SAMPLE', ''))
        if result != float(msize):
            raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the memory size'''))

    @secure_communication()
    def screen_dump(self, file, type='JPEG', background='BLACK', dir='E:\\',
                    area='FULLSCREEN'):
        ''' Initiate a screen dump

        Input:
        file(str) : destination filename, auto incremented
        type(str) : image type (PSD, BMP, BMPCOMP, JPEG (default), PNG, TIFF)
        background(str) : background color (BLACK (default), WHITE)
        dir(str) : destination directory (E:\\ is the default shared folder)
        area(str) : hardcopy area (GRIDAREAONLY, DSOWINDOW, FULLSCREEN)

        Output:
        '''
        mes = cleandoc('''HCSU DEV, {}, BCKG, {}, DEST, FILE, DIR, {}, FILE, {}
                       , AREA, {}; SCDP'''.format(type, background,
                                                  dir, file, area))
        self.write(mes)

    @secure_communication()
    def sequence(self, segments, max_size):
        ''' Set the sequence mode on and set number of segments, maximum memory
        size.
        Input:
        segments(int) : number of segments. max: 2000.
        max_size(float) : maximum memory length. Format:
        {10e3, 10.0e3, 11e+3, 25K, 10M (mili), 10MA (mega))

        Output:
        None
        '''
        self.write('SEQ ON, {}, {}'.format(segments, max_size))

DRIVERS = {'LeCroy64Xi': LeCroy64Xi}