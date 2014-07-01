# -*- coding: utf-8 -*-
"""
Created on Thu Jun 26 14:17:14 2014

@author: Pierre

Note :

"""

# LeCroy_354Xi.py class, to perform the communication between the Wrapper and the device

#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

from contextlib import contextmanager
from ..driver_tools import (BaseInstrument, InstrIOError, secure_communication,
                            instrument_property)
from ..visa_tools import VisaInstrument
from inspect import cleandoc
import types
import logging
import time


class LeCroyChannel(BaseInstrument):

    def __init__(self, LeCroy354A, channel_num, caching_allowed=True,
                 caching_permissions={}):
        super(LeCroyChannel, self).__init__(None, caching_allowed,
                                            caching_permissions)
        self._LeCroy = LeCroy354A
        self._channel = channel_num

    @contextmanager
    def secure(self):
        i = 0
        while not self._LeCroy.lock.acquire():
            time.sleep(0.1)
            i += 1
            if i > 50:
                raise InstrIOError
        try:
            yield
        finally:
            self._LeCroy.lock.release()

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
            result = self._LeCroy.ask('{}:VDIV?'.format(self._channel))
            result = result.replace('VDIV ', '')
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
        self._LeCroy.write('{}:VDIV {}' % (self._channel, value))
        result = self._LeCroy.ask('{}:VDIV?'.format(self._channel))
        result = result.replace('VDIV ', '')
        if result != value:
            raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the vertical'''))

    @secure_communication()
    def read_data(self):
        '''

        '''
        # ASCII format used to transfer the data
        self._LeCroy.write('DTFORM ASCII')
        # Select the trace to which the waveform is transfered.
        # Argument must be {CH1,CH2,CH3,CH4, MATH}
        if self._channel != 'M1':
            channel = 'CH{}'.format(self._channel[1])
        else:
            channel = 'MATH'
        self._LeCroy.write('WAVESRC {}'.format(channel))
        # read the waveform data. Format <ascii_block> <delimiter>
        # <ascii_block> contains block data.
        data = self.ask_for_values('DTWAVE?')
        infodata = self.ask('DTINF?')

        return data
        return infodata


class LeCroy354A(VisaInstrument):
    ''' This is the python driver for the LeCroy Waverunner 44Xi
    Digital Oscilloscope

    Usage:
    Initialize with
    <name>= instruments.create('name', 'LeCroy_44Xi', address='<VICP address>')
    <VICP address> = VICP::<ip-address>
    '''
    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super(LeCroy354A, self).__init__(connection_info,
                                         caching_allowed,
                                         caching_permissions,
                                         auto_open)

        ''' Initializes the LeCroy 44Xi.

        Input:
        None

        Output:
        None
        '''
        self._values = {}
        self.unitoftime = 'S'

        # Make Load/Delete Waveform functions for each channel
        for ch in range(1, 5):
            self._add_save_data_func(ch)

        self.get_all()

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
        defined_channels = ['C1', 'C2', 'C3', 'C4', 'M1']
        return defined_channels


    # Functions
    def get_all(self):
        ''' Get all parameter values

        '''
        self.get_timebase()
        self.get_ch1_vertical()
        self.get_ch2_vertical()
        self.get_ch3_vertical()
        self.get_ch4_vertical()
        self.get_msize()

    @instrument_property
    @secure_communication()
    def trigger_mode(self):
        ''' Method to get the trigger mode

        '''
        mode = self.ask_for_values('TRMD?')[0]
        if mode is not None:
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
        result = self.ask_for_values('TRMD?')[0]
        if result != value:
            raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the trigger mode'''))

#    @instrument_property
#    @secure_communication()
#    def time_unit_for_command(self):
#        ''' Get the time unit used for each command using time
#
#        '''
#        return '{}/DIV'.format(self.unitoftime)
#
#    @time_unit_for_command.setter
#    @secure_communication()
#    def time_unit_for_command(self, value):
#        ''' Method to set the unit of time
#
#        Input:
#        {'KS' for kilosecond,'S' for second, 'MS' for milisecond,
#        'US' for microsecond, 'NS' for nanosecond}
#        '''
#        self.unitoftime = '{}'.format(value)

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
        value_expected = '{}'.format(value)
        if result != value_expected:
            raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the timebase'''))


    def screen_capture(self, screen_type='PNG):
        ''' Initiate a screen dump

        Input:
        file(str) : destination filename, auto incremented
        type(str) : image type (PSD, BMP, BMPCOMP, JPEG (default), PNG, TIFF)
        background(str) : background color (BLACK (default), WHITE)
        dir(str) : destination directory (E:\\ is the default shared folder)
        area(str) : hardcopy area (GRIDAREAONLY, DSOWINDOW, FULLSCREEN)

        Output:
        <binary_block>
        '''
        logging.info(__name__ + ' : Take a screenshot with filename %s, type %s and save on harddisk %s' % (file, type, dir))
        self._visainstrument.write('HCSU DEV, %s, BCKG, %s, DEST, FILE, DIR, %s, FILE, %s, AREA, %s; SCDP' % (type, background, dir, file, area))
        # command returns : #8<byte_length><binary_block>
        screen = self.ask('TSCRN? {}'.format(screen_type))[10:]
        return screen

#    def _do_save_data(self, channel):
#        ''' Store a trace in ASCII format in internal memory
#
#        Input:
#        channel(int) : channel
#
#        Output:
#        None
#        '''
#        logging.info(__name__ + ' : Save data for channel %s' % channel)
#        self._visainstrument.write('STST C%s,HDD,AUTO,OFF,FORMAT,ASCII; STO' % channel)
#
#    def _add_save_data_func(self, channel):
#        ''' Adds save_ch[n]_data functions, based on _do_save_data(channel).
#        n = (1,2,3,4) for 4 channels.
#
#        '''
#        func = lambda: self._do_save_data(channel)
#        setattr(self, 'save_ch%s_data' % channel, func)
#
#    def sequence(self, segments, max_size):
#        ''' Set the sequence mode on and set number of segments, maximum memory size.
#        Input:
#        segments(int) : number of segments. max: 2000.
#        max_size(float) : maximum memory length. Format: {10e3, 10.0e3, 11e+3, 25K, 10M (mili), 10MA (mega))
#
#        Output:
#        None
#        '''
#        logging.info(__name__ + ' : Set the sequence mode settings. Segments: %s, Maximum memory size: %s' % (segments, max_size))
#        self._visainstrument.write('SEQ ON, %s, %s' % (segments, max_size))
#
#    def do_set_msize(self, msize):
#        ''' Set the current maximum memory length used to capture waveforms.
#        Input:
#        msize(float) : Max. memory length size in Samples.
#        Output:
#        None
#        '''
#        logging.info(__name__ + ' : Set maximum memory length to %s' % msize)
#        self._visainstrument.write('MSIZ %s' % msize)
#
#    def do_get_msize(self):
#        ''' Get the current maximum memory length used to capture waveforms.
#        Input:
#        None
#        Output:
#        result(float) : maximum memory size in Samples
#        '''
#        logging.info(__name__ + ' : Get maximum memory length')
#        result = self._visainstrument.ask('MSIZ?')
#        result = result.replace('MSIZ ', '')
#        result = result.replace(' SAMPLE', '')
#        return float(result)
