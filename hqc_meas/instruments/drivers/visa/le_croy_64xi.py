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


"""
from threading import Lock
from contextlib import contextmanager
from ..driver_tools import (BaseInstrument, InstrIOError, secure_communication,
                            instrument_property)
from ..visa_tools import VisaInstrument
from inspect import cleandoc
import time
import struct
import numpy as np


class LeCroyChannel(BaseInstrument):
    """
    """

    def __init__(self, LeCroy64Xi, channel_num, caching_allowed=True,
                 caching_permissions={}):
        super(LeCroyChannel, self).__init__(None, caching_allowed,
                                            caching_permissions)
        self._LeCroy64Xi = LeCroy64Xi
        self._channel = channel_num
        self.descriptor_start = 21
        self.data = {}

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

        Output:
        value (str) : Vertical base in V.
        '''
        with self.secure():
            # check if the channel studied is not a trace channel
            if len(self._channel) == 1:
                result = self._LeCroy64Xi.ask('C{}:VDIV?'
                                              .format(self._channel))
                result = result.replace('C{}:VDIV '.format(self._channel), '')
                return result
            else:
                mes = '{} is a trace and not a channel'.format(self._channel)
                raise InstrIOError(mes)

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
            # check if the channel studied is not a trace channel
            if len(self._channel) == 1:
                self._LeCroy64Xi.write('C{}:VDIV {}'
                                       .format(self._channel, value))
                result = self._LeCroy64Xi.ask('C{}:VDIV?'
                                              .format(self._channel))
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
                    raise InstrIOError(cleandoc('''Instrument did not set
                                                correctly the verticalbase'''))
            else:
                mes = '{} is a trace and not a channel'.format(self._channel)
                raise InstrIOError(mes)

    @instrument_property
    @secure_communication()
    def vertical_offset(self):
        ''' Get vertical offset in Volts of the channel

        Input:
        None

        Output:
        value (str) : Vertical offset in V.
        '''
        with self.secure():
            # check if the channel studied is not a trace channel
            if len(self._channel) == 1:
                result = self._LeCroy64Xi.ask('C{}:OFST?'
                                              .format(self._channel))
                result = result.replace('C{}:OFST '.format(self._channel), '')
                result = result.replace('V', '')
                return result
            else:
                mes = '{} is a trace and not a channel'.format(self._channel)
                raise InstrIOError(mes)

    @vertical_offset.setter
    @secure_communication()
    def vertical_offset(self, value):
        ''' Set vertical offset in Volts of the channel

        Input:
        value (str) : Vertical offset in V. (UV (microvolts), MV (milivolts),
        V (volts) or KV (kilovolts))
        (Example: '20E-3', '20 MV')

        Output:
        None
        '''
        with self.secure():
            # check if the channel studied is not a trace channel
            if len(self._channel) == 1:
                self._LeCroy64Xi.write('C{}:OFST {}'
                                       .format(self._channel, value))
                result = self._LeCroy64Xi.ask('C{}:OFST?'
                                              .format(self._channel))
                result = result.replace('C{}:OFST '.format(self._channel), '')
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
                    raise InstrIOError(cleandoc('''Instrument did not set
                                                correctly the verticalbase'''))
            else:
                mes = '{} is a trace and not a channel'.format(self._channel)
                raise InstrIOError(mes)

    @secure_communication()
    def sweep(self):
        ''' Get the number of sweeps of the channel

        Input:
        None

        Output:
        value (str)
        '''
        instr = self._LeCroy64Xi
        with self.secure():
            # check if the channel studied is not a trace channel
            if len(self._channel) == 1:
                cmd = 'VBS? "return=app.Acquisition.C{}.Out.Result.Sweeps"'
                result = instr.ask_for_values(cmd.format(self._channel))
                if result:
                    return result[0]
                else:
                    raise InstrIOError('LeCraoy failed to return sweep')
            else:
                mes = '{} is a trace and not a channel'.format(self._channel)
                raise InstrIOError(mes)

    @secure_communication()
    def do_save_data(self, destination='HDD', mode='OFF', format='ASCII'):
        ''' Store a trace in ASCII format in internal memory

        Input:
        destination = {'CARD', 'FLPY', 'HDD', 'M1', 'M2', 'M3', 'M4'}
        mode = {'OFF', 'WRAP', 'FILL'}
        format = {'BINARY', 'SPREADSHEET', 'MATLAB', 'MATHCAD'}

        Output:
        None
        '''
        with self.secure():
            # check if the channel studied is not a trace channel
            if len(self._channel) == 1:
                self._LeCroy64Xi.write('STST C{},{},AUTO,{},FORMAT,{}; STO'
                                       .format(self._channel, destination,
                                               mode, format))
            else:
                self._LeCroy64Xi.write('STST {},{},AUTO,{},FORMAT,{}; STO'
                                       .format(self._channel, destination,
                                               mode, format))

    @secure_communication()
    def add_save_data_func(self):
        ''' Adds save_ch[n]_data functions, based on _do_save_data(channel).
        n = (1,2,3,4) for 4 channels.

        '''
        with self.secure():
            func = lambda: self.do_save_data(self._channel)
            setattr(self, 'save_ch{}_data'.format(self._channel), func)

    @secure_communication()
    def read_data_complete(self, hires):
        '''
        Input:
        {'True', 'Yes', 'No', 'False'}

        Output:
        Library self.data :
            many parameters in string
            vertical values data : 'Volt_Value_array'
            horizontal values data : 'SingleSweepTimesValuesArray' or
                                     'SEQNCEWaveformTimesValuesArray'
        '''
        if hires in ('True', 'Yes'):
            self._LeCroy64Xi.write('CFMT DEF9,WORD,BIN')
            result = self._LeCroy64Xi.ask('CFMT?')
            if result != 'CFMT DEF9,WORD,BIN':
                mes = 'Instrument did not set the WORD mode'
                raise InstrIOError(mes)
        elif hires in ('No', 'False'):
            self._LeCroy64Xi.write('CFMT DEF9,BYTE,BIN')
            result = self._LeCroy64Xi.ask('CFMT?')
            if result != 'CFMT DEF9,BYTE,BIN':
                mes = 'Instrument did not set the BYTE mode'
                raise InstrIOError(mes)
        else:
            mes = "{} is not an allowed input. Input:{'True', 'Yes', 'No', 'False'}".format(hires)
            raise InstrIOError(mes)

        if len(self._channel) == 1:
            databyte = bytearray(self._LeCroy64Xi.ask('C{}:WF?'.format(self._channel)))
        else:
            databyte = bytearray(self._LeCroy64Xi.ask('{}:WF?'.format(self._channel)))

        databyte = databyte[self.descriptor_start:]
        self.data['COMM_TYPE'] = struct.unpack('<b', databyte[32:33])  # /COMM_TYPE: enum ; chosen by remote command COMM_FORMAT
        self.data['COMM_ORDER'] = struct.unpack('<b', databyte[34:35])  # COMM_ORDER: enum

#        'The following variables of this basic wave descriptor block specify
#        ' the block lengths of all blocks of which the entire waveform (as it is
#        ' currently being read) is composed. If a block length is zero, this
#        ' block is (currently) not present.
#
#        ' Blocks and arrays that are present will be found in the same order
#        ' as their descriptions below.

        # BLOCKS:
        self.data['WAVE_DESCRIPTOR'] = struct.unpack('<i', databyte[36:40])  # WAVE_DESCRIPTOR: long ; length in bytes of block WAVEDESC
        self.data['USER_TEXT'] = struct.unpack('<i', databyte[40:44])  # USER_TEXT: long ; length in bytes of block USERTEXT
        self.data['RES_DESC1'] = struct.unpack('<i', databyte[44:48])  # RES_DESC1: long
        # ARRAYS:
        self.data['TRIGTIME_ARRAY'] = struct.unpack('<i', databyte[48:52])  # TRIGTIME_ARRAY: long ; length in bytes of TRIGTIME array
        self.data['RIS_TIME_ARRAY'] = struct.unpack('<i', databyte[52:56])  # RIS_TIME_ARRAY: long ; length in bytes of RIS_TIME array
        self.data['RES_ARRAY1'] = struct.unpack('<i', databyte[56:60])  # RES_ARRAY1: long ; an expansion entry is reserved
        self.data['WAVE_ARRAY_1'] = struct.unpack('<i', databyte[60:64])  # WAVE_ARRAY_1: long ; length in bytes of 1st simple data array. In transmitted waveform, represent the number of transmitted bytes in accordance with the NP parameter of the WFSU remote command and the used format (see COMM_TYPE).

        self.data['WAVE_ARRAY_2'] = struct.unpack('<i', databyte[64:68])  # WAVE_ARRAY_2: long ; length in bytes of 2nd simple data array
        self.data['RES_ARRAY2'] = struct.unpack('<i', databyte[68:72])  # RES_ARRAY2: long
        self.data['RES_ARRAY3'] = struct.unpack('<i', databyte[72:76])  # RES_ARRAY3: long ; 2 expansion entries are reserved

        # The following variables identify the instrument
        self.data['INSTRUMENT_NAME'] = databyte[76:92]  # INSTRUMENT_NAME: string
        self.data['INSTRUMENT_NUMBER'] = struct.unpack('<i', databyte[92:96])  # INSTRUMENT_NUMBER: long
        self.data['TRACE_LABEL'] = databyte[96:112]  # /TRACE_LABEL: string ; identifies the waveform.
#        '<112> RESERVED1: word
#        '<114> RESERVED2: word ; 2 expansion entries

        # The following variables describe the waveform and the time at which the waveform was generated.
        self.data['WAVE_ARRAY_COUNT'] = struct.unpack('<i', databyte[116:120])  # WAVE_ARRAY_COUNT: long ; number of data points in the data array. If there are two data arrays (FFT or Extrema), this number applies to each array separately.
        self.data['PNTS_PER_SCREEN'] = struct.unpack('<i', databyte[120:124])  # PNTS_PER_SCREEN: long ; nominal number of data points on the screen
        self.data['FIRST_VALID_PNT'] = struct.unpack('<i', databyte[124:128])  # FIRST_VALID_PNT: long ; count of number of points to skip before first good point FIRST_VALID_POINT = 0 for normal waveforms.
        self.data['LAST_VALID_PNT'] = struct.unpack('<i', databyte[128:132])  # LAST_VALID_PNT: long ; index of last good data point in record before padding (blanking) was started. LAST_VALID_POINT = WAVE_ARRAY_COUNT-1 except for aborted sequence and rollmode acquisitions
        self.data['FIRST_POINT'] = struct.unpack('<i', databyte[132:136])  # FIRST_POINT: long ; for input and output, indicates the offset relative to the beginning of the trace buffer. Value is the same as the FP parameter of the WFSU remote command.
        self.data['STARTING_FACTOR'] = struct.unpack('<i', databyte[136:140])  # SPARSING_FACTOR: long ; for input and output, indicates the sparsing into the transmitted data block. Value is the same as the SP parameter of the WFSU remote command.
        self.data['SEGMENT_INDEX'] = struct.unpack('<i', databyte[140:144])  # SEGMENT_INDEX: long ; for input and output, indicates the index of the transmitted segment. Value is the same as the SN parameter of the WFSU remote command.
        self.data['SUBARRAY_COUNT'] = struct.unpack('<i', databyte[144:148])  # SUBARRAY_COUNT: long ; for Sequence, acquired segment count, between 0 and NOM_SUBARRAY_COUNT
        self.data['SWEEPS_PER_ACQ'] = struct.unpack('<i', databyte[148:152])  # SWEEPS_PER_ACQ: long ; for Average or Extrema, number of sweeps accumulated else 1

        self.data['POINTS_PER_PAIR'] = struct.unpack('<h', databyte[152:154])  # POINTS_PER_PAIR: word ; for Peak Detect waveforms (which always include data points in DATA_ARRAY_1 and min/max pairs in DATA_ARRAY_2). Value is the number of data points for each min/max pair.
        self.data['PAIR_OFFSET'] = struct.unpack('<h', databyte[154:156])  # PAIR_OFFSET: word ; for Peak Detect waveforms only Value is the number of data points by which the first min/max pair in DATA_ARRAY_2 is offset relative to the first data value in DATA_ARRAY_1.
        self.data['VERTICAL_GAIN'] = struct.unpack('<f', databyte[156:160])  # VERTICAL_GAIN: float
        self.data['VERTICAL_OFFSET'] = struct.unpack('<f', databyte[160:164])  # VERTICAL_OFFSET: float ; to get floating values from raw data : VERTICAL_GAIN * data - VERTICAL_OFFSET
        self.data['MAX_VALUE'] = struct.unpack('<f', databyte[164:168])  # MAX_VALUE: float ; maximum allowed value. It corresponds to the upper edge of the grid.
        self.data['MIN_VALUE'] = struct.unpack('<f', databyte[168:172])  # MIN_VALUE: float ; minimum allowed value. It corresponds to the lower edge of the grid.
        self.data['NOMINAL_BITS'] = struct.unpack('<h', databyte[172:174])  # NOMINAL_BITS: word ; a measure of the intrinsic precision of the observation: ADC data is 8 bit averaged data is 10-12 bit, etc.
        self.data['NOM_SUBARRAY_COUNT'] = struct.unpack('<h', databyte[174:176])  # NOM_SUBARRAY_COUNT: word ; for Sequence, nominal segment count else 1
        self.data['HORIZ_INTERVAL'] = struct.unpack('<f', databyte[176:180])  # HORIZ_INTERVAL: float ; sampling interval for time domain waveforms
        self.data['HORIZ_OFFSET'] = struct.unpack('<d', databyte[180:188])  # HORIZ_OFFSET: double ; trigger offset for the first sweep of the trigger, seconds between the trigger and the first data point
        self.data['PIXEL_OFFSET'] = struct.unpack('<d', databyte[188:196])  # PIXEL_OFFSET: double ; needed to know how to display the waveform

        self.data['VERTUNIT'] = databyte[196:244]  # VERTUNIT: unit_definition ; units of the vertical axis;INSTRUMENT_NAME: string
        self.data['HORUNIT'] = databyte[244:292]  # HORUNIT: unit_definition ; units of the horizontal axis

        self.data['HORIZ_UNCERTAINTY'] = struct.unpack('<f', databyte[292:296])  # HORIZ_UNCERTAINTY: float ; uncertainty from one acquisition to the next, of the horizontal offset in seconds

        self.data['TRIGGER_TIME_seconds'] = struct.unpack('<d', databyte[296:304])  # TRIGGER_TIME: time_stamp ; time of the trigger
        self.data['TRIGGER_TIME_minutes'] = struct.unpack('<b', databyte[304:305])  # TRIGGER_TIME: time_stamp ; time of the trigger
        self.data['TRIGGER_TIME_hours'] = struct.unpack('<b', databyte[305:306])  # TRIGGER_TIME: time_stamp ; time of the trigger
        self.data['TRIGGER_TIME_days'] = struct.unpack('<b', databyte[306:307])  # TRIGGER_TIME: time_stamp ; time of the trigger
        self.data['TRIGGER_TIME_months'] = struct.unpack('<b', databyte[307:308])  # TRIGGER_TIME: time_stamp ; time of the trigger
        self.data['TRIGGER_TIME_year'] = struct.unpack('<h', databyte[308:310])  # TRIGGER_TIME: time_stamp ; time of the trigger

        self.data['ACQ_DURATION'] = struct.unpack('<f', databyte[312:316])  # ACQ_DURATION: float ; duration of the acquisition (in sec) in multi-trigger waveforms. (e.g. sequence, RIS, or averaging)
        self.data['RECORD_TYPE'] = struct.unpack('<h', databyte[316:318])
        # RECORD_TYPE:
#        'enum
#        '_0(single_sweep)
#        '_1(interleaved)
#        '_2(histogram)
#        '_3(graph)
#        '_4(filter_coefficient)
#        '_5(complex)
#        '_6(extrema)
#        '_7(sequence_obsolete)
#        '_8(centered_RIS)
#        '_9(peak_)

        self.data['PROCESSING_DONE'] = struct.unpack('<h', databyte[318:320])
        # PROCESSING_DONE:
#        'enum
#        '_0 no_processing
#        '_1 fir_filter
#        '_2 interpolated
#        '_3 sparsed
#        '_4 autoscaled
#        '_5 no_result
#        '_6 rolling
#        '_7 cumulative

        self.data['RIS_SWEEPS'] = struct.unpack('<h', databyte[322:324])  # RIS_SWEEPS: word ; for RIS, the number of sweeps else 1

        # The following variables describe the basic acquisition conditions used when the waveform was acquired
        self.data['TIMEBASE'] = struct.unpack('<h', databyte[324:326])
        # TIMEBASE: enum
#        '_0 1_ps/div
#        '_1 2_ps/div
#        '_2 5_ps/div
#        '_3 10_ps/div
#        '_4 20_ps/div
#        '_5 50_ps/div
#        '_6 100_ps/div
#        '_7 200_ps/div
#        '_8 500_ps/div
#        '_9 1_ns/div
#        '_10 2_ns/div
#        '_11 5_ns/div
#        '_12 10_ns/div
#        '_13 20_ns/div
#        '_14 50_ns/div
#        '_15 100_ns/div
#        '_16 200_ns/div
#        '_17 500_ns/div
#        '_18 1_us/div
#        '_19 2_us/div
#        '_20 5_us/div
#        '_21 10_us/div
#        '_22 20_us/div
#        '_23 50_us/div
#        '_24 100_us/div
#        '_25 200_us/div
#        '_26 500_us/div
#        '_27 1_ms/div
#        '_28 2_ms/div
#        '_29 5_ms/div
#        '_30 10_ms/div
#        '_31 20_ms/div
#        '_32 50_ms/div
#        '_33 100_ms/div
#        '_34 200_ms/div
#        '_35 500_ms/div
#        '_36 1_s/div
#        '_37 2_s/div
#        '_38 5_s/div
#        '_39 10_s/div
#        '_40 20_s/div
#        '_41 50_s/div
#        '_42 100_s/div
#        '_43 200_s/div
#        '_44 500_s/div
#        '_45 1_ks/div
#        '_46 2_ks/div
#        '_47 5_ks/div
#        '_100(EXTERNAL)

        self.data['VERT_COUPLING'] = struct.unpack('<h', databyte[326:328])
        # VERT_COUPLING: enum
#        '_0(DC_50_Ohms)
#        '_1(ground)
#        '_2(DC_1MOhm)
#        '_3(ground)
#        '_4(AC, _1MOhm)

        self.data['PROBE_ATT'] = struct.unpack('<f', databyte[328:332])  # PROBE_ATT: float
        self.data['FIXED_VERT_GAIN'] = struct.unpack('<h', databyte[332:334])
        # FIXED_VERT_GAIN: enum
#        '_0 1_uV/div
#        '_1 2_uV/div
#        '_2 5_uV/div
#        '_3 10_uV/div
#        '_4 20_uV/div
#        '_5 50_uV/div
#        '_6 100_uV/div
#        '_7 200_uV/div
#        '_8 500_uV/div
#        '_9 1_mV/div
#        '_10 2_mV/div
#        '_11 5_mV/div
#        '_12 10_mV/div
#        '_13 20_mV/div
#        '_14 50_mV/div
#        '_15 100_mV/div
#        '_16 200_mV/div
#        '_17 500_mV/div
#        '_18 1_V/div
#        '_19 2_V/div
#        '_20 5_V/div
#        '_21 10_V/div
#        '_22 20_V/div
#        '_23 50_V/div
#        '_24 100_V/div
#        '_25 200_V/div
#        '_26 500_V/div
#        '_27 1_kV/div

        self.data['BANDWIDTH_LIMIT'] = struct.unpack('<h', databyte[334:336])
        # BANDWIDTH_LIMIT: enum
#        '_0(off)
#        '_1 on

        self.data['VERTICAL_VERNIER'] = struct.unpack('<f', databyte[336:340])  # VERTICAL_VERNIER: float
        self.data['TACQ_VERT_OFFET'] = struct.unpack('<f', databyte[340:344])  # ACQ_VERT_OFFSET: float
        self.data['WAVE_SOURCE'] = struct.unpack('<h', databyte[344:346])
        # WAVE_SOURCE: enum
#        '_0(CHANNEL_1)
#        '_1(CHANNEL_2)
#        '_2(CHANNEL_3)
#        '_3(CHANNEL_4)

        # Get the vertical values :
        waveform_size = self.data['WAVE_ARRAY_COUNT'][0]
        waveform_starting_point = self.data['WAVE_DESCRIPTOR'][0] + self.data['TRIGTIME_ARRAY'][0]
        self.data['Volt_Value_array'] = np.empty(waveform_size)
        if hires in ('Yes', 'True'):
            Values16 = np.empty(waveform_size, dtype=np.int16)
            for i in range(0, waveform_size-1):
                Values16[i] = struct.unpack('<h', databyte[(waveform_starting_point+2*i):(waveform_starting_point+2*i+2)])[0]
                self.data['Volt_Value_array'][i] = self.data['VERTICAL_GAIN'][0] * Values16[i] + self.data['VERTICAL_OFFSET'][0]
        else:
            Values8 = np.empty(waveform_size, dtype=np.int8)
            for i in range(0, waveform_size-1):
                Values8[i] = struct.unpack('<b', databyte[(waveform_starting_point+i):(waveform_starting_point+i+1)])[0]
                self.data['Volt_Value_array'][i] = self.data['VERTICAL_GAIN'][0] * Values8[i] + self.data['VERTICAL_OFFSET'][0]

        # Get the horizontal values :
        # Single Sweep waveforms: x[i] = HORIZ_INTERVAL x i + HORIZ_OFFSET
        if self.data['TRIGTIME_ARRAY'][0] == 0:  # if the TrigArray lentgh is null, it tells us, it's a simple single sweep waveform
            self.data['SingleSweepTimesValuesArray'] = np.empty(waveform_size)
            for i in range(0,waveform_size-1):
                self.data['SingleSweepTimesValuesArray'][i] = self.data['HORIZ_INTERVAL'][0] * i + self.data['HORIZ_OFFSET'][0]
        else:
            self.data['TrigTimeCount'] = np.empty(self.data['TRIGTIME_ARRAY'][0] / 16)
            self.data['TrigTimeOffset'] = np.empty(self.data['TRIGTIME_ARRAY'][0] / 16)
            for i in range(0, self.data['TRIGTIME_ARRAY'][0] / 16 - 1):
                self.data['TrigTimeCount'][i] = struct.unpack('<d', databyte[(self.data['WAVE_DESCRIPTOR'][0]+i*16):(self.data['WAVE_DESCRIPTOR'][0]+8+i*16)])[0]
                self.data['TrigTimeOffset'][i] = struct.unpack('<d', databyte[(self.data['WAVE_DESCRIPTOR'][0]+8+i*16):(self.data['WAVE_DESCRIPTOR'][0]+16+i*16)])[0]
            self.data['SEQNCEWaveformTimesValuesArray'] = np.empty(waveform_size)
            # Array of horizontal values
            for n in range(0, len(self.data['TrigTimeCount']) - 1):
                for i in range(0, waveform_size / len(self.data['TrigTimeCount']) - 1):
                    self.data['SEQNCEWaveformTimesValuesArray'][n * (waveform_size / len(self.data['TrigTimeCount'])) + i] = self.data['HORIZ_INTERVAL'][0] * i + self.data['TrigTimeOffset'][n]

        return self.data

    @secure_communication()
    def read_data_cfast(self, hires):
        '''
        Input:
        {'True', 'Yes', 'No', 'False'}

        Output:
        Library self.data :
            many parameters in string
            vertical values data : 'Volt_Value_array'
            horizontal values data : 'SingleSweepTimesValuesArray' or
                                     'SEQNCEWaveformTimesValuesArray'
        '''
        if hires in ('True', 'Yes'):
            self._LeCroy64Xi.write('CFMT DEF9,WORD,BIN')
            result = self._LeCroy64Xi.ask('CFMT?')
            if result != 'CFMT DEF9,WORD,BIN':
                mes = 'Instrument did not set the WORD mode'
                raise InstrIOError(mes)
        elif hires in ('No', 'False'):
            self._LeCroy64Xi.write('CFMT DEF9,BYTE,BIN')
            result = self._LeCroy64Xi.ask('CFMT?')
            if result != 'CFMT DEF9,BYTE,BIN':
                mes = 'Instrument did not set the BYTE mode'
                raise InstrIOError(mes)
        else:
            mes = "{} is not an allowed input. Input:{'True', 'Yes', 'No', 'False'}".format(hires)
            raise InstrIOError(mes)

        if len(self._channel) == 1:
            databyte = bytearray(self._LeCroy64Xi.ask('C{}:WF?'.format(self._channel)))
        else:
            databyte = bytearray(self._LeCroy64Xi.ask('{}:WF?'.format(self._channel)))

        databyte = databyte[self.descriptor_start:]

        # BLOCKS:
        self.data['WAVE_DESCRIPTOR'] = struct.unpack('<i', databyte[36:40])  # WAVE_DESCRIPTOR: long ; length in bytes of block WAVEDESC
        # ARRAYS:
        self.data['TRIGTIME_ARRAY'] = struct.unpack('<i', databyte[48:52])  # TRIGTIME_ARRAY: long ; length in bytes of TRIGTIME array


        # The following variables describe the waveform and the time at which the waveform was generated.
        self.data['WAVE_ARRAY_COUNT'] = struct.unpack('<i', databyte[116:120])  # WAVE_ARRAY_COUNT: long ; number of data points in the data array. If there are two data arrays (FFT or Extrema), this number applies to each array separately.
        self.data['PNTS_PER_SCREEN'] = struct.unpack('<i', databyte[120:124])  # PNTS_PER_SCREEN: long ; nominal number of data points on the screen
        self.data['FIRST_VALID_PNT'] = struct.unpack('<i', databyte[124:128])  # FIRST_VALID_PNT: long ; count of number of points to skip before first good point FIRST_VALID_POINT = 0 for normal waveforms.
        self.data['LAST_VALID_PNT'] = struct.unpack('<i', databyte[128:132])  # LAST_VALID_PNT: long ; index of last good data point in record before padding (blanking) was started. LAST_VALID_POINT = WAVE_ARRAY_COUNT-1 except for aborted sequence and rollmode acquisitions
        self.data['FIRST_POINT'] = struct.unpack('<i', databyte[132:136])  # FIRST_POINT: long ; for input and output, indicates the offset relative to the beginning of the trace buffer. Value is the same as the FP parameter of the WFSU remote command.
        self.data['STARTING_FACTOR'] = struct.unpack('<i', databyte[136:140])  # SPARSING_FACTOR: long ; for input and output, indicates the sparsing into the transmitted data block. Value is the same as the SP parameter of the WFSU remote command.
        self.data['SEGMENT_INDEX'] = struct.unpack('<i', databyte[140:144])  # SEGMENT_INDEX: long ; for input and output, indicates the index of the transmitted segment. Value is the same as the SN parameter of the WFSU remote command.
        self.data['SUBARRAY_COUNT'] = struct.unpack('<i', databyte[144:148])  # SUBARRAY_COUNT: long ; for Sequence, acquired segment count, between 0 and NOM_SUBARRAY_COUNT
        self.data['SWEEPS_PER_ACQ'] = struct.unpack('<i', databyte[148:152])  # SWEEPS_PER_ACQ: long ; for Average or Extrema, number of sweeps accumulated else 1

        self.data['POINTS_PER_PAIR'] = struct.unpack('<h', databyte[152:154])  # POINTS_PER_PAIR: word ; for Peak Detect waveforms (which always include data points in DATA_ARRAY_1 and min/max pairs in DATA_ARRAY_2). Value is the number of data points for each min/max pair.
        self.data['PAIR_OFFSET'] = struct.unpack('<h', databyte[154:156])  # PAIR_OFFSET: word ; for Peak Detect waveforms only Value is the number of data points by which the first min/max pair in DATA_ARRAY_2 is offset relative to the first data value in DATA_ARRAY_1.
        self.data['VERTICAL_GAIN'] = struct.unpack('<f', databyte[156:160])  # VERTICAL_GAIN: float
        self.data['VERTICAL_OFFSET'] = struct.unpack('<f', databyte[160:164])  # VERTICAL_OFFSET: float ; to get floating values from raw data : VERTICAL_GAIN * data - VERTICAL_OFFSET
        self.data['MAX_VALUE'] = struct.unpack('<f', databyte[164:168])  # MAX_VALUE: float ; maximum allowed value. It corresponds to the upper edge of the grid.
        self.data['MIN_VALUE'] = struct.unpack('<f', databyte[168:172])  # MIN_VALUE: float ; minimum allowed value. It corresponds to the lower edge of the grid.
        self.data['NOMINAL_BITS'] = struct.unpack('<h', databyte[172:174])  # NOMINAL_BITS: word ; a measure of the intrinsic precision of the observation: ADC data is 8 bit averaged data is 10-12 bit, etc.
        self.data['NOM_SUBARRAY_COUNT'] = struct.unpack('<h', databyte[174:176])  # NOM_SUBARRAY_COUNT: word ; for Sequence, nominal segment count else 1
        self.data['HORIZ_INTERVAL'] = struct.unpack('<f', databyte[176:180])  # HORIZ_INTERVAL: float ; sampling interval for time domain waveforms
        self.data['HORIZ_OFFSET'] = struct.unpack('<d', databyte[180:188])  # HORIZ_OFFSET: double ; trigger offset for the first sweep of the trigger, seconds between the trigger and the first data point
        self.data['PIXEL_OFFSET'] = struct.unpack('<d', databyte[188:196])  # PIXEL_OFFSET: double ; needed to know how to display the waveform

        self.data['VERTUNIT'] = databyte[196:244]  # VERTUNIT: unit_definition ; units of the vertical axis;INSTRUMENT_NAME: string
        self.data['HORUNIT'] = databyte[244:292]  # HORUNIT: unit_definition ; units of the horizontal axis

        self.data['HORIZ_UNCERTAINTY'] = struct.unpack('<f', databyte[292:296])  # HORIZ_UNCERTAINTY: float ; uncertainty from one acquisition to the next, of the horizontal offset in seconds

        self.data['TRIGGER_TIME_seconds'] = struct.unpack('<d', databyte[296:304])  # TRIGGER_TIME: time_stamp ; time of the trigger
        self.data['TRIGGER_TIME_minutes'] = struct.unpack('<b', databyte[304:305])  # TRIGGER_TIME: time_stamp ; time of the trigger
        self.data['TRIGGER_TIME_hours'] = struct.unpack('<b', databyte[305:306])  # TRIGGER_TIME: time_stamp ; time of the trigger
        self.data['TRIGGER_TIME_days'] = struct.unpack('<b', databyte[306:307])  # TRIGGER_TIME: time_stamp ; time of the trigger
        self.data['TRIGGER_TIME_months'] = struct.unpack('<b', databyte[307:308])  # TRIGGER_TIME: time_stamp ; time of the trigger
        self.data['TRIGGER_TIME_year'] = struct.unpack('<h', databyte[308:310])  # TRIGGER_TIME: time_stamp ; time of the trigger

        self.data['ACQ_DURATION'] = struct.unpack('<f', databyte[312:316])  # ACQ_DURATION: float ; duration of the acquisition (in sec) in multi-trigger waveforms. (e.g. sequence, RIS, or averaging)
        self.data['RECORD_TYPE'] = struct.unpack('<h', databyte[316:318])
        # RECORD_TYPE:
#        'enum
#        '_0(single_sweep)
#        '_1(interleaved)
#        '_2(histogram)
#        '_3(graph)
#        '_4(filter_coefficient)
#        '_5(complex)
#        '_6(extrema)
#        '_7(sequence_obsolete)
#        '_8(centered_RIS)
#        '_9(peak_)

        self.data['PROCESSING_DONE'] = struct.unpack('<h', databyte[318:320])
        # PROCESSING_DONE:
#        'enum
#        '_0 no_processing
#        '_1 fir_filter
#        '_2 interpolated
#        '_3 sparsed
#        '_4 autoscaled
#        '_5 no_result
#        '_6 rolling
#        '_7 cumulative

        self.data['RIS_SWEEPS'] = struct.unpack('<h', databyte[322:324])  # RIS_SWEEPS: word ; for RIS, the number of sweeps else 1

        # The following variables describe the basic acquisition conditions used when the waveform was acquired
        self.data['TIMEBASE'] = struct.unpack('<h', databyte[324:326])
        # TIMEBASE: enum
#        '_0 1_ps/div
#        '_1 2_ps/div
#        '_2 5_ps/div
#        '_3 10_ps/div
#        '_4 20_ps/div
#        '_5 50_ps/div
#        '_6 100_ps/div
#        '_7 200_ps/div
#        '_8 500_ps/div
#        '_9 1_ns/div
#        '_10 2_ns/div
#        '_11 5_ns/div
#        '_12 10_ns/div
#        '_13 20_ns/div
#        '_14 50_ns/div
#        '_15 100_ns/div
#        '_16 200_ns/div
#        '_17 500_ns/div
#        '_18 1_us/div
#        '_19 2_us/div
#        '_20 5_us/div
#        '_21 10_us/div
#        '_22 20_us/div
#        '_23 50_us/div
#        '_24 100_us/div
#        '_25 200_us/div
#        '_26 500_us/div
#        '_27 1_ms/div
#        '_28 2_ms/div
#        '_29 5_ms/div
#        '_30 10_ms/div
#        '_31 20_ms/div
#        '_32 50_ms/div
#        '_33 100_ms/div
#        '_34 200_ms/div
#        '_35 500_ms/div
#        '_36 1_s/div
#        '_37 2_s/div
#        '_38 5_s/div
#        '_39 10_s/div
#        '_40 20_s/div
#        '_41 50_s/div
#        '_42 100_s/div
#        '_43 200_s/div
#        '_44 500_s/div
#        '_45 1_ks/div
#        '_46 2_ks/div
#        '_47 5_ks/div
#        '_100(EXTERNAL)

        self.data['VERT_COUPLING'] = struct.unpack('<h', databyte[326:328])
        # VERT_COUPLING: enum
#        '_0(DC_50_Ohms)
#        '_1(ground)
#        '_2(DC_1MOhm)
#        '_3(ground)
#        '_4(AC, _1MOhm)

        self.data['PROBE_ATT'] = struct.unpack('<f', databyte[328:332])  # PROBE_ATT: float
        self.data['FIXED_VERT_GAIN'] = struct.unpack('<h', databyte[332:334])
        # FIXED_VERT_GAIN: enum
#        '_0 1_uV/div
#        '_1 2_uV/div
#        '_2 5_uV/div
#        '_3 10_uV/div
#        '_4 20_uV/div
#        '_5 50_uV/div
#        '_6 100_uV/div
#        '_7 200_uV/div
#        '_8 500_uV/div
#        '_9 1_mV/div
#        '_10 2_mV/div
#        '_11 5_mV/div
#        '_12 10_mV/div
#        '_13 20_mV/div
#        '_14 50_mV/div
#        '_15 100_mV/div
#        '_16 200_mV/div
#        '_17 500_mV/div
#        '_18 1_V/div
#        '_19 2_V/div
#        '_20 5_V/div
#        '_21 10_V/div
#        '_22 20_V/div
#        '_23 50_V/div
#        '_24 100_V/div
#        '_25 200_V/div
#        '_26 500_V/div
#        '_27 1_kV/div

        self.data['BANDWIDTH_LIMIT'] = struct.unpack('<h', databyte[334:336])
        # BANDWIDTH_LIMIT: enum
#        '_0(off)
#        '_1 on

        self.data['VERTICAL_VERNIER'] = struct.unpack('<f', databyte[336:340])  # VERTICAL_VERNIER: float
        self.data['TACQ_VERT_OFFET'] = struct.unpack('<f', databyte[340:344])  # ACQ_VERT_OFFSET: float
        self.data['WAVE_SOURCE'] = struct.unpack('<h', databyte[344:346])
        # WAVE_SOURCE: enum
#        '_0(CHANNEL_1)
#        '_1(CHANNEL_2)
#        '_2(CHANNEL_3)
#        '_3(CHANNEL_4)

        # Get the vertical values :
        waveform_size = self.data['WAVE_ARRAY_COUNT'][0]
        waveform_starting_point = self.data['WAVE_DESCRIPTOR'][0] + self.data['TRIGTIME_ARRAY'][0]
        self.data['Volt_Value_array'] = np.empty(waveform_size)
        if hires in ('Yes', 'True'):
            Values16 = np.empty(waveform_size, dtype=np.int16)
            for i in range(0, waveform_size-1):
                Values16[i] = struct.unpack('<h', databyte[(waveform_starting_point+2*i):(waveform_starting_point+2*i+2)])[0]
                self.data['Volt_Value_array'][i] = self.data['VERTICAL_GAIN'][0] * Values16[i] + self.data['VERTICAL_OFFSET'][0]
        else:
            Values8 = np.empty(waveform_size, dtype=np.int8)
            for i in range(0, waveform_size-1):
                Values8[i] = struct.unpack('<b', databyte[(waveform_starting_point+i):(waveform_starting_point+i+1)])[0]
                self.data['Volt_Value_array'][i] = self.data['VERTICAL_GAIN'][0] * Values8[i] + self.data['VERTICAL_OFFSET'][0]

        # Get the horizontal values :
        # Single Sweep waveforms: x[i] = HORIZ_INTERVAL x i + HORIZ_OFFSET
        if self.data['TRIGTIME_ARRAY'][0] == 0:  # if the TrigArray lentgh is null, it tells us, it's a simple single sweep waveform
            self.data['SingleSweepTimesValuesArray'] = np.empty(waveform_size)
            for i in range(0,waveform_size-1):
                self.data['SingleSweepTimesValuesArray'][i] = self.data['HORIZ_INTERVAL'][0] * i + self.data['HORIZ_OFFSET'][0]
        else:
            self.data['TrigTimeCount'] = np.empty(self.data['TRIGTIME_ARRAY'][0] / 16)
            self.data['TrigTimeOffset'] = np.empty(self.data['TRIGTIME_ARRAY'][0] / 16)
            for i in range(0, self.data['TRIGTIME_ARRAY'][0] / 16 - 1):
                self.data['TrigTimeCount'][i] = struct.unpack('<d', databyte[(self.data['WAVE_DESCRIPTOR'][0]+i*16):(self.data['WAVE_DESCRIPTOR'][0]+8+i*16)])[0]
                self.data['TrigTimeOffset'][i] = struct.unpack('<d', databyte[(self.data['WAVE_DESCRIPTOR'][0]+8+i*16):(self.data['WAVE_DESCRIPTOR'][0]+16+i*16)])[0]
            self.data['SEQNCEWaveformTimesValuesArray'] = np.empty(waveform_size)
            # Array of horizontal values
            for n in range(0, len(self.data['TrigTimeCount']) - 1):
                for i in range(0, waveform_size / len(self.data['TrigTimeCount']) - 1):
                    self.data['SEQNCEWaveformTimesValuesArray'][n * (waveform_size / len(self.data['TrigTimeCount'])) + i] = self.data['HORIZ_INTERVAL'][0] * i + self.data['TrigTimeOffset'][n]

        return self.data



class LeCroy64Xi(VisaInstrument):
    """ This is the python driver for the LeCroy Waverunner 64Xi
    Digital Oscilloscope


    """
    caching_permissions = {'defined_channels': True}

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super(LeCroy64Xi, self).__init__(connection_info,
                                         caching_allowed,
                                         caching_permissions,
                                         auto_open)

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
        """ {'1', '2', '3', '4'} are the real channel of the instrument
        {'TA', 'TB', 'TC', 'TD'} are the trace calculated from the channel.
        It is only useful for the property do_save_data.
        Same thing for 'ALL_DISPLAYED'
        """
        defined_channels = ['1', '2', '3', '4', 'TA', 'TB', 'TC', 'TD',
                            'ALL_DISPLAYED']
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
    def auto_calibrate(self):
        ''' Method to know if the instrument is in auto calibrate mode

        '''
        answer = self.ask('ACAL?')
        if answer is not None:
            answer = answer.replace('ACAL ', '')
            return answer
        else:
            mes = 'LeCroy 354A did not return its answer'
            raise InstrIOError(mes)

    @auto_calibrate.setter
    @secure_communication()
    def auto_calibrate(self, value):
        ''' Method to set the trigger mode

        Input:
        {'ON', 'Yes', 'OFF', 'No'}
        '''
        if value in ('ON', 'Yes'):
            self.write('ACAL ON')
            result = self.ask('ACAL?')
            result = result.replace('ACAL ', '')
            if result != 'ON':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                            the auto calibrate mode'''))
        elif value in ('OFF', 'No'):
            self.write('ACAL OFF')
            result = self.ask('ACAL?')
            result = result.replace('ACAL ', '')
            if result != 'OFF':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                            the auto calibrate mode'''))
        else:
            mes = '{} is not an allowed value'.format(value)
            raise InstrIOError(mes)

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

    @secure_communication()
    def clear_sweeps(self):
        ''' restart the cumulative processing:
        Input:
        None

        Output:
        None
        '''
        self.write('CLSW')

DRIVERS = {'LeCroy64Xi': LeCroy64Xi}
