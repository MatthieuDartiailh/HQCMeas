# -*- coding: utf-8 -*-
#==============================================================================
# module : agilent_psa.py
# author : Benjamin Huard
# license : MIT license
#==============================================================================
"""
This module defines drivers for agilent PSA.

:Contains:
    SpecDescriptor
    AgilentPSA

"""
from inspect import cleandoc
import numpy as np
from ..driver_tools import (InstrIOError, secure_communication,
                            instrument_property)
from ..visa_tools import VisaInstrument


DATA_FORMATTING_DICT = {'raw I/Q data': 0,
                        'descriptor': 1,
                        '(I,Q) vs time': 3,
                        'log(mag) vs freq': 4,
                        'average of log(mag) vs freq': 7,
                        'mag vs freq in Vrms': 11,
                        'average of mag vs freq in Vrms': 12}


class SpecDescriptor():
    def __init__(self):
        self.initialized = False
        self.FFTpeak = 0
        self.FFTfreq = 0
        self.FFTnbrSteps = 2
        self.Firstfreq = 0
        self.Freqstep = 0
        self.TimenbrSteps = 2
        self.firsttime = 0
        self.TimeStep = 0.1
        self.timedomaincheck = 1
        self.totaltime = 1.0
        self.averagenbr = 1


class AgilentPSA(VisaInstrument):
    """
    """
    caching_permissions = {'start_frequency_SA': False,
                           'stop_frequency_SA': False,
                           'mode': False}

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super(AgilentPSA, self).__init__(connection_info,
                                         caching_allowed,
                                         caching_permissions,
                                         auto_open)
        self.write("ROSC:SOURCE EXT")  # 10 MHz clock bandwidth external
        self.write("ROSC:OUTP ON")  # 10 MHz clock bandwidth internal ON
        self.write("FORM:DATA ASCii")  # lots of data must be read in
                                       # ASCii format
        self.write("FORM:BORD NORMAL")  # (TO CHECK)
        self.mode = self.mode  # initialize PSA properly if SPEC or WAV mode
        self.spec_header = SpecDescriptor()

    @secure_communication(2)
    def get_spec_header(self):
        """
        """
        if self.mode == 'SPEC':
            answer = self.ask_for_values("FETCH:SPEC1?")
            if answer:
                self.spec_header.initialized = True
                self.spec_header.FFTpeak = answer[0]
                self.spec_header.FFTfreq = answer[1]/1e9
                self.spec_header.FFTnbrSteps = answer[2]
                self.spec_header.Firstfreq = answer[3]/1e9
                self.spec_header.Freqstep = answer[4]/1e9
                self.spec_header.TimenbrSteps = answer[5]
                self.spec_header.firsttime = answer[6]
                self.spec_header.TimeStep = answer[7]
                self.spec_header.timedomaincheck = answer[8]
                self.spec_header.totaltime = answer[9]
                self.spec_header.averagenbr = answer[10]
            else:
                raise InstrIOError(cleandoc('''Agilent PSA did not return its
                        mode'''))
        else:
            raise '''PSA is not in Spectrum mode'''

    @secure_communication()
    def read_data(self, trace):
        """
        """
        DATA_FORMAT = ['raw I/Q data', 'descriptor', '0', '(I,Q) vs time',
                       'log(mag) vs freq', '0', '0',
                       'average of log(mag) vs freq', '0', '0', '0',
                       'mag vs freq in Vrms', 'average of mag vs freq in Vrms']
        if self.mode == 'SA':

            # must be read in ASCii format
            self.write("FORM:DATA ASCii")
            # stop all the measurements
            self.write(":ABORT")
            # go to the "Single sweep" mode
            self.write(":INIT:CONT OFF")
            # initiate measurement
            self.write(":INIT")

            #
            self.ask_for_values("SWEEP:TIME?")

            self.write("*WAI")  # SA waits until the averaging is done
            # Loop to see when the averaging is done
            while True:
                try:
                    self.ask_for_values("SWEEP:TIME?")
                    break
                except:
                    pass

            data = self.ask_for_values('trace? trace{}'.format(trace))

            if data:
                freq = np.linspace(self.start_frequency_SA,
                                   self.stop_frequency_SA,
                                   self.sweep_points_SA)
                return np.rec.fromarrays([freq, np.array(data)],
                                         names=['Frequency',
                                                DATA_FORMAT[trace]])
            else:
                raise InstrIOError(cleandoc('''Agilent PSA did not return the
                    trace {} data'''.format(trace)))

        elif self.mode == 'SPEC':
            self.get_spec_header()
            self.write("INIT:IMM;*WAI")  # start the acquisition and wait until
                                         # over
            # Check how *OPC? works
            self.ask("*OPC?")
            data = self.ask_for_values("FETCH:SPEC{}?".format(trace))
            if data:
                if trace in (4, 7, 11, 12):
                    header = self.spec_header
                    stop = header.Firstfreq +\
                        header.Freqstep*(header.FFTnbrSteps-1)
                    freq = np.linspace(header.Firstfreq, stop,
                                       header.FFTnbrSteps)
                    return np.rec.fromarrays([freq, np.array(data)],
                                             names=['Freq',
                                                    DATA_FORMAT[trace]])
                elif trace in (0, 3):
                    header = self.spec_header
                    stop = header.firsttime +\
                        header.TimeStep*(header.TimenbrSteps-1)
                    freq = np.linspace(header.firsttime, stop,
                                       header.TimenbrSteps)
                    return np.rec.fromarrays([freq, np.array(data)],
                                             names=['Time',
                                                    DATA_FORMAT[trace]])
                else:
                    raise InstrIOError(cleandoc('''Wrong parameters for trace
                                                in Agilent E4440'''))

            else:
                raise InstrIOError(cleandoc('''Agilent PSA did not return the
                    trace data'''))
        else:
            self.get_spec_header()
            self.write("INIT:IMM;*WAI")  # start the acquisition and wait until
                                         # over
            #Check how *OPC? works
            self.ask("*OPC?")
            data = self.ask_for_values("FETCH:WAV0?")  # this will get the
                                                # (I,Q) as a function of freq
            if data:
                return np.rec.fromarrays([data[::2], data[1::2]],
                                         'Q', 'I')
                # one should get all the even indices (Q)
                # and odd indices (I) separately
            else:
                raise InstrIOError(cleandoc('''Agilent PSA did not return the
                    trace data'''))

    @instrument_property
    @secure_communication()
    def mode(self):
        """
        """
        SAorBASIC = self.ask('inst:sel?')
        if SAorBASIC == 'SA':
            return 'SA'
        elif SAorBASIC == 'BASIC':
            conf = self.ask('conf?')
            if conf:
                return conf  # SPEC if basic mode with spectral density
                            # or WAV if basic mode with time domain
            else:
                raise InstrIOError(cleandoc('''Agilent PSA did not return its
                    mode'''))
        else:
            raise InstrIOError(cleandoc('''Agilent PSA did not return its
                    mode'''))

    @mode.setter
    @secure_communication()
    def mode(self, value):
        """
        """
        if value == 'SPEC':
            self.write('INST:SEL BASIC')
            self.write('CONF:SPECTRUM')
            self.write("INIT:CONT ON")  # set in  continuous mode
            self.write("SENS:SPEC:IFP WIDE")  # set the wide bandWidth 80MHz
                                              # for spectrum
            self.write("SENS:SPEC:AVER OFF")  # set the average off
                                              # for spectrum
            self.write("INIT:CONT OFF")  # set in single sweep mode
            self.write("INIT:IMM")
        elif value == "WAV":
            self.write('INST:SEL BASIC')
            self.write('CONF:WAV')
            self.write("SENS:WAV:IFP WIDE")  # set the wide bandWidth 80MHz
                                             # for timedomain
            self.write("SENS:WAV:AVER OFF")  # set the average off
                                             # for timedomain
            self.write("SENS:WAV:ADC:DITHER OFF")  # dither signal off
            self.write("INIT:CONT OFF")  # set in single sweep mode
            self.write("INIT:IMM")
        else:
            self.write('INST:SEL SA')

    @instrument_property
    @secure_communication()
    def start_frequency_SA(self):
        """Start frequency getter method

        """

        if self.mode == 'SA':
            freq = self.ask_for_values('FREQ:STAR?')
            if freq:
                return freq[0]/1e9
            else:
                raise InstrIOError(cleandoc('''Agilent PSA did not return the
                    start frequency'''))
        elif self.mode == 'SPEC':
            if not self.spec_header.initialized:
                self.get_spec_header()

            return self.spec_header.Firstfreq

        else:
            raise '''PSA is not in the appropriate mode to get correctly the
                    start frequency'''

    @start_frequency_SA.setter
    @secure_communication()
    def start_frequency_SA(self, value):
        """Start frequency setter method
        """
        if self.mode == 'SA':
            self.write('FREQ:STAR {} GHz'.format(value))
            result = self.ask_for_values('FREQ:STAR?')
            if result:
                if abs(result[0]/1e9 - value)/value > 10**-12:
                    raise InstrIOError(cleandoc('''PSA did not set correctly
                    the start frequency'''))
            else:
                raise InstrIOError(cleandoc('''PSA did not set correctly the
                    start frequency'''))
        else:
            raise '''PSA is not in the appropriate mode to set correctly the
                    start frequency'''

    @instrument_property
    @secure_communication()
    def stop_frequency_SA(self):
        """Stop frequency getter method
        """
        if self.mode == 'SA':
            freq = self.ask_for_values('FREQ:STOP?')
            if freq:
                return freq[0]/1e9
            else:
                raise InstrIOError(cleandoc('''Agilent PSA did not return the
                    stop frequency'''))

        else:
            raise '''PSA is not in the appropriate mode to get correctly the
                    stop frequency'''

    @stop_frequency_SA.setter
    @secure_communication()
    def stop_frequency_SA(self, value):
        """Stop frequency setter method

        """
        if self.mode == 'SA':
            self.write('FREQ:STOP {} GHz'.format(value))
            result = self.ask_for_values('FREQ:STOP?')
            if result:
                if abs(result[0]/1e9 - value)/value > 10**-12:
                    raise InstrIOError(cleandoc('''PSA did not set correctly
                    the stop frequency'''))
            else:
                raise InstrIOError(cleandoc('''PSA did not set correctly the
                    stop frequency'''))
        else:
            raise '''PSA is not in the appropriate mode to set correctly the
                    stop frequency'''

    @instrument_property
    @secure_communication()
    def center_frequency(self):
        """Center frequency getter method

        """

        freq = self.ask_for_values('FREQ:CENT?')
        if freq:
            return freq[0]/1e9
        else:
            raise InstrIOError(cleandoc('''Agilent PSA did not return the
                    center frequency'''))

    @center_frequency.setter
    @secure_communication()
    def center_frequency(self, value):
        """center frequency setter method

        """

        self.write('FREQ:CENT {} GHz'.format(value))
        result = self.ask_for_values('FREQ:CENT?')
        if result:
            if abs(result[0]/1e9 - value)/value > 10**-12:
                raise InstrIOError(cleandoc('''PSA did not set correctly the
                    center frequency'''))
        else:
            raise InstrIOError(cleandoc('''PSA did not set correctly the
                    center frequency'''))

    @instrument_property
    @secure_communication()
    def span_frequency(self):
        """Span frequency getter method

        """

        if self.mode == 'SPEC':
            freq = self.ask_for_values('SENS:SPEC:FREQ:SPAN?')
            if freq:
                return freq[0]/1e9
            else:
                raise InstrIOError(cleandoc('''Agilent PSA did not return the
                    span frequency'''))
        elif self.mode == 'SA':
            freq = self.ask_for_values('FREQ:SPAN?')
            if freq:
                return freq[0]/1e9
            else:
                raise InstrIOError(cleandoc('''Agilent PSA did not return the
                    span frequency'''))

        else:
            raise '''PSA is not in the appropriate mode to get correctly the
                    span frequency'''

    @span_frequency.setter
    @secure_communication()
    def span_frequency(self, value):
        """span frequency setter method
        """
        if self.mode == 'SA':
            self.write('FREQ:SPAN {} GHz'.format(value))
            result = self.ask_for_values('FREQ:SPAN?')
            if result:
                if abs(result[0]/1e9 - value)/value > 10**-12:
                    raise InstrIOError(cleandoc('''PSA did not set correctly
                    the span frequency'''))
            else:
                raise InstrIOError(cleandoc('''PSA did not set correctly the
                    span frequency'''))

        elif self.mode == 'SPEC':
            self.write('SENS:SPEC:FREQ:SPAN {} GHz'.format(value))
            result = self.ask_for_values('SENS:SPEC:FREQ:SPAN?')
            if result:
                if abs(result[0]/1e9 - value)/value > 10**-12:
                    raise InstrIOError(cleandoc('''PSA did not set correctly
                    the span frequency'''))
            else:
                raise InstrIOError(cleandoc('''PSA did not set correctly the
                    span frequency'''))

        else:
            raise '''PSA is not in the appropriate mode to set correctly the
                    span frequency'''

    @instrument_property
    @secure_communication()
    def sweep_time(self):
        """Sweep time getter method
        """

        if self.mode == 'WAV':
            sweep = self.ask_for_values('SENS:WAV:SWEEP:TIME?')
            if sweep:
                return sweep[0]
            else:
                raise InstrIOError(cleandoc('''Agilent PSA did not return the
                    sweep time'''))
        elif self.mode == 'SA':
            sweep = self.ask_for_values('SWEEP:TIME?')
            if sweep:
                return sweep[0]
            else:
                raise InstrIOError(cleandoc('''Agilent PSA did not return the
                    sweep time'''))
        else:
            raise '''PSA is not in the appropriate mode to get correctly the
                    sweep time'''

    @sweep_time.setter
    @secure_communication()
    def sweep_time(self, value):
        """sweep time setter method
        """

        if self.mode == 'WAV':
            self.write('SENS:WAV:SWEEP:TIME {}'.format(value))
            result = self.ask_for_values('SENS:WAV:SWEEP:TIME?')
            if result:
                if abs(result[0] - value)/value > 10**-12:
                    raise InstrIOError(cleandoc('''PSA did not set correctly
                    the sweep time'''))
            else:
                raise InstrIOError(cleandoc('''PSA did not set correctly the
                    sweep time'''))
        elif self.mode == 'SA':
            self.write('SWEEP:TIME {}'.format(value))
            result = self.ask_for_values('SWEEP:TIME?')
            if result:
                if abs(result[0] - value)/value > 10**-12:
                    raise InstrIOError(cleandoc('''PSA did not set correctly
                    the sweep time'''))
            else:
                raise InstrIOError(cleandoc('''PSA did not set correctly the
                    sweep time'''))
        else:
            raise '''PSA is not in the appropriate mode to set correctly the
                    sweep time'''

    @instrument_property
    @secure_communication()
    def RBW(self):
        """
        """
        if self.mode == 'WAV':
            rbw = self.ask_for_values('SENS:WAV:BWIDTH?')
            if rbw:
                return rbw[0]
            else:
                raise InstrIOError(cleandoc('''Agilent PSA did not return the
                    RBW'''))
        elif self.mode == 'SPEC':
            rbw = self.ask_for_values('SENS:SPEC:BWIDTH?')
            if rbw:
                return rbw[0]
            else:
                raise InstrIOError(cleandoc('''Agilent PSA did not return the
                    RBW'''))
        else:
            rbw = self.ask_for_values('BWIDTH?')
            if rbw:
                return rbw[0]
            else:
                raise InstrIOError(cleandoc('''Agilent PSA did not return the
                    channel Resolution bandwidth'''))

    @RBW.setter
    @secure_communication()
    def RBW(self, value):
        """
        """
        if self.mode == 'WAV':
            self.write('SENS:WAV:BWIDTH {}'.format(value))
            result = self.ask_for_values('SENS:WAV:BWIDTH?')
            if result:
                if abs(result[0] > value) > 10**-12:
                    raise InstrIOError(cleandoc('''PSA did not set correctly
                    the channel Resolution bandwidth'''))
            else:
                raise InstrIOError(cleandoc('''PSA did not set correctly the
                    channel Resolution bandwidth'''))

        elif self.mode == 'SPEC':
            self.write('SENS:SPEC:BWIDTH {}'.format(value))
            result = self.ask_for_values('SENS:SPEC:BWIDTH?')
            if result:
                if abs(result[0] > value) > 10**-12:
                    raise InstrIOError(cleandoc('''PSA did not set correctly
                    the channel Resolution bandwidth'''))
            else:
                raise InstrIOError(cleandoc('''PSA did not set correctly the
                    channel Resolution bandwidth'''))
        else:
            self.write('BAND {}'.format(value))
            result = self.ask_for_values('BWIDTH?')
            if result:
                if abs(result[0] > value) > 10**-12:
                    raise InstrIOError(cleandoc('''PSA did not set correctly
                    the channel Resolution bandwidth'''))
            else:
                raise InstrIOError(cleandoc('''PSA did not set correctly the
                    channel Resolution bandwidth'''))

    @instrument_property
    @secure_communication()
    def VBW_SA(self):
        """
        """
        if self.mode == 'SA':

            vbw = self.ask_for_values('BAND:VID?')
            if vbw:
                return vbw[0]
            else:
                raise InstrIOError(cleandoc('''Agilent PSA did not return the
                    channel Video bandwidth'''))
        else:
            raise '''PSA is not in the appropriate mode to set correctly the
                    sweep time'''

    @VBW_SA.setter
    @secure_communication()
    def VBW_SA(self, value):
        """
        """
        if self.mode == 'WAV':
            raise InstrIOError(cleandoc('''PSA did not set correctly the
                    channel Resolution bandwidth'''))
        elif self.mode == 'SPEC':
            raise InstrIOError(cleandoc('''PSA did not set correctly the
                    channel Resolution bandwidth'''))
        else:
            self.write('BAND:VID {}'.format(value))
            result = self.ask_for_values('BAND:VID?')
            if result:
                if abs(result[0] > value) > 10**-12:
                    raise InstrIOError(cleandoc('''PSA did not set correctly
                    the channel Video bandwidth'''))
            else:
                raise InstrIOError(cleandoc('''PSA did not set correctly the
                    channel Video bandwidth'''))

    @instrument_property
    @secure_communication()
    def sweep_points_SA(self):
        """
        """
        points = self.ask_for_values('SENSe:SWEep:POINts?')
        if points:
            return points[0]
        else:
            raise InstrIOError(cleandoc('''Agilent PSA did not return the
                    sweep point number'''))

    @sweep_points_SA.setter
    @secure_communication()
    def sweep_points_SA(self, value):
        """
        """
        self.write('SENSe:SWEep:POINts {}'.format(value))
        result = self.ask_for_values('SENSe:SWEep:POINts?')
        if result:
            if result[0] != value:
                raise InstrIOError(cleandoc('''PSA did not set correctly the
                    sweep point number'''))
        else:
            raise InstrIOError(cleandoc('''PSA did not set correctly the
                    sweep point number'''))

    @instrument_property
    @secure_communication()
    def average_count_SA(self):
        """
        """
        count = self.ask_for_values('AVERage:COUNt?')
        if count:
            return count[0]
        else:
            raise InstrIOError(cleandoc('''Agilent PSA did not return the
                     average count'''))

    @average_count_SA.setter
    @secure_communication()
    def average_count_SA(self, value):
        """
        """
        self.write('AVERage:COUNt {}'.format(value))
        result = self.ask_for_values('AVERage:COUNt?')
        if result:
            if result[0] != value:
                raise InstrIOError(cleandoc('''PSA did not set correctly the
                     average count'''))
        else:
            raise InstrIOError(cleandoc('''PSA did not set correctly the
                     average count'''))

    @instrument_property
    @secure_communication()
    def average_state_SA(self):
        """
        """
        mode = self.ask('AVERage?')
        if mode:
            return mode
        else:
            raise InstrIOError(cleandoc('''Agilent PSA did not return the
                    average state'''))

    @average_state_SA.setter
    @secure_communication()
    def average_state_SA(self, value):
        """
        """
        self.write('AVERage:STATE {}'.format(value))
        result = self.ask('AVERage?')

        if result.lower() != value.lower()[:len(result)]:
            raise InstrIOError(cleandoc('''PSA did not set correctly the
                average state'''))


DRIVERS = {'AgilentPSA': AgilentPSA}
