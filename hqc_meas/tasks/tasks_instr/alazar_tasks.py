# -*- coding: utf-8 -*-
# =============================================================================
# module : alazar_tasks.py
# author : Benjamin Huard
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
    freq = Str().tag(pref=True)

    timeaftertrig = Str().tag(pref=True)

    tracesbuffer = Str().tag(pref=True)

    averagenumber = Str().tag(pref=True)

    average = Bool(True).tag(pref=True)

    driver_list = ['Alazar935x']

    task_database_entries = set_default({'AI': {}, 'AQ': {},
                                         'BI': {}, 'BQ': {}})

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(DemodAlazarTask, self).check(*args,
                                                             **kwargs)

        if (self.format_and_eval_string(self.averagenumber) %
                self.format_and_eval_string(self.tracesbuffer)) != 0:
            test = False
            traceback[self.task_path + '/' + self.task_name + '-get_demod'] = \
                cleandoc('''The number of buffers used must be an integer.''')

        if int(self.format_and_eval_string(self.freq) *
               self.format_and_eval_string(self.timeaftertrig)) == 0:
            test = False
            traceback[self.task_path + '/' + self.task_name + '-get_demod'] = \
                cleandoc('''Cannot acquire for an integer
                            number of periods. Use longer times.''')

        return test, traceback

    def perform(self):
        """
        """
        if not self.driver:
            self.start_driver()

        if self.driver.owner != self.task_name:
            self.driver.owner = self.task_name

        self.driver.configure_board()

        average = self.format_and_eval_string(self.averagenumber)
        recordsPerCapture = int(max(1000, average))

        recordsPerBuffer = int(self.format_and_eval_string(self.tracesbuffer))
        answer = self.driver.get_demod(
            self.format_and_eval_string(self.timeaftertrig)*10**-6,
            recordsPerCapture, recordsPerBuffer,
            self.format_and_eval_string(self.freq)*10**6, self.average
            )
        AI, AQ, BI, BQ = answer

        self.write_in_database('AI', AI)
        self.write_in_database('AQ', AQ)
        self.write_in_database('BI', BI)
        self.write_in_database('BQ', BQ)


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
