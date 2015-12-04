# -*- coding: utf-8 -*-
# =============================================================================
# module : alazar_tasks.py
# author : Benjamin Huard & Sébastien Jezouin
# license : MIT license
# =============================================================================
"""

"""
from atom.api import (Str, Bool, set_default)
from inspect import cleandoc
import numpy as np

from hqc_meas.tasks.api import InstrumentTask


class DemodAlazarTask(InstrumentTask):
    """ Get the raw or averaged quadratures of the signal.

    """
    freq = Str('40').tag(pref=True)
    
    freqB = Str('40').tag(pref=True)
 
    timeaftertrig = Str('0').tag(pref=True)
    
    timeaftertrigB = Str('0').tag(pref=True)
    
    duration = Str('1000').tag(pref=True)
    
    durationB = Str('0').tag(pref=True)
    
    samplingtime = Str('1000').tag(pref=True)
    
    samplingtimeB = Str('0').tag(pref=True)

    tracesbuffer = Str('100').tag(pref=True)

    tracesnumber = Str('1000').tag(pref=True)

    average = Bool(True).tag(pref=True)

    IQtracemode = Bool(False).tag(pref=True)

    driver_list = ['Alazar935x']

    task_database_entries = set_default({'Demod': {}})

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(DemodAlazarTask, self).check(*args,
                                                             **kwargs)

        if (self.format_and_eval_string(self.tracesnumber) %
                self.format_and_eval_string(self.tracesbuffer) != 0 ):
            test = False
            traceback[self.task_path + '/' + self.task_name + '-get_demod'] = \
                cleandoc('''The number of traces must be an integer multiple of the number of traces per buffer.''')
                
        if not (self.format_and_eval_string(self.tracesnumber) >= 1000):
            test = False
            traceback[self.task_path + '/' + self.task_name + '-get_demod'] = \
                cleandoc('''At least 1000 traces must be recorded. Please take real measurements and not noisy craps.''')

        startaftertrig = [self.format_and_eval_string(elem) for elem in self.timeaftertrig.split(',')]
        duration = [self.format_and_eval_string(elem) for elem in self.duration.split(',')]
        tablesamplingtime = [self.format_and_eval_string(elem) for elem in self.samplingtime.split(',')]
        tablesamplingtimeB = [self.format_and_eval_string(elem) for elem in self.samplingtimeB.split(',')]
        startaftertrigB = [self.format_and_eval_string(elem) for elem in self.timeaftertrigB.split(',')]
        durationB = [self.format_and_eval_string(elem) for elem in self.durationB.split(',')]
        
        if len(startaftertrig) != len(duration):
            test = False
            traceback[self.task_path + '/' + self.task_name + '-get_demod'] = \
                cleandoc('''An equal number of "Start time after trig" and "Duration" should be given for channel A.''')
        else :
            for st, dur, tot in zip(startaftertrig, duration, tablesamplingtime):
                if not (st >= 0 and dur >= 0 and tot >= 0) :
                       test = False
                       traceback[self.task_path + '/' + self.task_name + '-get_demod'] = \
                           cleandoc('''Both "Start time after trig" and "Durations" must be >= 0 on channel A.''')
                           
        if len(startaftertrigB) != len(durationB):
            test = False
            traceback[self.task_path + '/' + self.task_name + '-get_demod'] = \
                cleandoc('''An equal number of "Start time after trig" and "Duration" should be given for channel B.''')
        else :
            for st, dur, tot in zip(startaftertrigB, durationB, tablesamplingtimeB):
                if not (st >= 0 and dur >= 0 and tot >= 0) :
                       test = False
                       traceback[self.task_path + '/' + self.task_name + '-get_demod'] = \
                           cleandoc('''Both "Start time after trig" and "Duration" must be >= 0 on channel B.''')

        if ((0 in duration) and (0 in durationB)):
            test = False
            traceback[self.task_path + '/' + self.task_name + '-get_demod'] = \
                           cleandoc('''You cannot disable both channel A and channel B. What would you measure stupid ?''')

        if self.IQtracemode:
            if (len(startaftertrig) != 1) or (len(startaftertrigB) != 1):
                test = False
                traceback[self.task_path + '/' + self.task_name + '-get_demod'] = \
                cleandoc('''In IQtrace mode, a single time step and initial time is required, not a list of them''')
            elif self.format_and_eval_string(tablesamplingtime[0]) / 1000.0 * self.format_and_eval_string(self.freq) % 1.0 != 0.0:
                test = False
                traceback[self.task_path + '/' + self.task_name + '-get_demod'] = \
                cleandoc('''Please modify the IQtrace time step so that 
                            it corresponds to an integer number of periods
                            in the demodulation.''')
            elif self.format_and_eval_string(tablesamplingtimeB[0]) / 1000.0 * self.format_and_eval_string(self.freqB) % 1.0 != 0.0:
                test = False
                traceback[self.task_path + '/' + self.task_name + '-get_demod'] = \
                cleandoc('''Please modify the IQtrace time step so that 
                            it corresponds to an integer number of periods
                            in the demodulation.''')
                            
        return test, traceback

    def perform(self):
        """
        """
        if not self.driver:
            self.start_driver()

        if self.driver.owner != self.task_name:
            self.driver.owner = self.task_name

        self.driver.configure_board()

        recordsPerCapture = self.format_and_eval_string(self.tracesnumber)
        recordsPerBuffer = int(self.format_and_eval_string(self.tracesbuffer))

        if self.IQtracemode:
            startaftertrigA = \
                np.arange(self.format_and_eval_string(self.timeaftertrig)*10.0**-9,
                          self.format_and_eval_string(self.duration)*10.0**-9,
                          self.format_and_eval_string(self.samplingtime)*10.0**-9).tolist()
            startaftertrigB = \
                np.arange(self.format_and_eval_string(self.timeaftertrigB)*10.0**-9,
                          self.format_and_eval_string(self.durationB)*10.0**-9,
                          self.format_and_eval_string(self.samplingtime)*10.0**-9).tolist()
        else:
            startaftertrigA = []
            for elem in self.timeaftertrig.split(','):
                startaftertrigA.append(self.format_and_eval_string(elem)*10.0**-9)
            startaftertrigB = []
            for elem in self.timeaftertrigB.split(','):
                startaftertrigB.append(self.format_and_eval_string(elem)*10.0**-9)
            durationA = []
            for elem in self.duration.split(','):
                durationA.append(self.format_and_eval_string(elem)*10.0**-9)
            durationB = []
            for elem in self.durationB.split(','):
                durationB.append(self.format_and_eval_string(elem)*10.0**-9)
    
        if 0 in durationA:
            NdemodA = 0
            NdemodB = len(durationB)
            duration = durationB
            startaftertrig = startaftertrigB
        elif 0 in durationB:
            NdemodB = 0
            NdemodA = len(durationA)
            duration = durationA
            startaftertrig = startaftertrigA
        else:
            NdemodA = len(durationA)
            NdemodB = len(durationB)
            duration = durationA + durationB
            startaftertrig = startaftertrigA + startaftertrigB

        freqA = self.format_and_eval_string(self.freq)*10.0**6
        freqB = self.format_and_eval_string(self.freqB)*10.0**6
        freq = [freqA] * NdemodA + [freqB] * NdemodB
        
        answer = self.driver.get_demod(startaftertrig, duration,
                                       recordsPerCapture, recordsPerBuffer,
                                       freq, self.average,
                                       NdemodA, NdemodB)
        
        self.write_in_database('Demod', answer)


class TracesAlazarTask(InstrumentTask):
    """ Get the raw or averaged traces of the signal.

    """

    timeaftertrig = Str().tag(pref=True)

    tracesnumber = Str().tag(pref=True)

    tracesbuffer = Str().tag(pref=True)

    average = Bool(True).tag(pref=True)

    driver_list = ['Alazar935x']

    task_database_entries = set_default({'traceA': np.zeros((1, 1)),
                                         'traceB': np.zeros((1, 1))})

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(TracesAlazarTask, self).check(*args,
                                                              **kwargs)

        if (self.format_and_eval_string(self.tracesnumber) %
                self.format_and_eval_string(self.tracesbuffer)) != 0:
            test = False
            traceback[self.task_path + '/' + self.task_name + '-get_traces'] =\
                cleandoc('''The number of buffers used must be an integer.''')

        return test, traceback

    def perform(self):
        """
        """
        if not self.driver:
            self.start_driver()

        if self.driver.owner != self.task_name:
            self.driver.owner = self.task_name

        self.driver.configure_board()

        recordsPerCapture = int(max(1000,
                            self.format_and_eval_string(self.tracesnumber)))

        recordsPerBuffer = int(self.format_and_eval_string(self.tracesbuffer))

        answer = self.driver.get_traces(
            self.format_and_eval_string(self.timeaftertrig)*10**-6,
            recordsPerCapture, recordsPerBuffer, self.average
            )

        traceA, traceB = answer
        self.write_in_database('traceA', traceA)
        self.write_in_database('traceB', traceB)

KNOWN_PY_TASKS = [DemodAlazarTask, TracesAlazarTask]
