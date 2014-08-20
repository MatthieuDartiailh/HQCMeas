# -*- coding: utf-8 -*-
# =============================================================================
# module : apply_mag_field_task.py
# author : Benjamin Huard
# license : MIT license
# =============================================================================
"""

"""
from atom.api import (Str, Int, set_default, Enum)
from inspect import cleandoc
import numpy as np

from hqc_meas.tasks.api import InstrumentTask


class PSAGetTrace(InstrumentTask):
    """ Get the trace displayed on the Power Spectrum Analyzer.

    """
    trace = Int(1).tag(pref=True)

    driver_list = ['AgilentPSA']
    task_database_entries = set_default({'trace_data': np.array([1.0]),
                                         'PSA_config': ''})

    def perform(self):
        """
        """
        if not self.driver:
            self.start_driver()

        if self.driver.owner != self.task_name:
            self.driver.owner = self.task_name

        sweep_modes = {'SA': 'Spectrum Analyzer',
                       'SPEC': 'Basic Spectrum Analyzer',
                       'WAV': 'Waveform'}

        PSA_config = 'Start freq' + self.driver.start_freq + \
                     'Stop freq' + self.driver.stop_freq + \
                     'Span freq' + self.driver.span_frequency + \
                     'Center freq' + self.driver.center_frequency + \
                     'Average number' + self.driver.average_count_SA + \
                     'Resolution bandwidth' + self.driver.RBW + \
                     'Video bandwidth' + self.driver.VBW_SA + \
                     'Number of points' + self.driver.sweep_points_SA + \
                     'Mode' + sweep_modes[self.mode]

        self.write_in_database('PSA_config', PSA_config)
        self.write_in_database('trace_data', self.driver.read_data(self.trace))

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(PSAGetTrace, self).check(*args, **kwargs)

        if self.trace > 4 or self.trace < 1:
            test = False
            traceback[self.task_path + '/' + self.task_name + '-get_trace'] = \
                cleandoc('''Trace number {} is not valid.
                         '''.format(self.trace))

        return test, traceback


class PSASetParam(InstrumentTask):
    """ Set important parameters of the Power Spectrum Analyzer.

    """
    trace = Int(1).tag(pref=True)

    mode = Enum('Start/Stop', 'Center/Span').tag(pref=True)

    start_freq = Str().tag(pref=True)

    end_freq = Str().tag(pref=True)

    center_freq = Str().tag(pref=True)

    span_freq = Str().tag(pref=True)

    average_nb = Str().tag(pref=True)

    resolution_bandwidth = Str().tag(pref=True)

    video_bandwidth = Str().tag(pref=True)

    driver_list = ['AgilentPSA']
    task_database_entries = set_default({'PSA_config': ''})

    def perform(self):
        """
        """
        if not self.driver:
            self.start_driver()

        if self.driver.owner != self.task_name:
            self.driver.owner = self.task_name

        if self.mode == 'Start/Stop':
            if self.start_freq:
                self.driver.start_freq = \
                    self.format_and_eval_string(self.start_freq)

            if self.stop_freq:
                self.driver.stop_freq = \
                    self.format_and_eval_string(self.stop_freq)
# start_freq is set again in case the former value of stop prevented to do it
            if self.start_freq:
                self.driver.start_freq = \
                    self.format_and_eval_string(self.start_freq)
        else:
            if self.center_freq:
                self.driver.center_frequency = \
                    self.format_and_eval_string(self.center_freq)

            if self.span_freq:
                self.driver.span_frequency = \
                    self.format_and_eval_string(self.span_freq)
# center_freq is set again in case the former value of span prevented to do it
            if self.center_freq:
                self.driver.center_frequency = \
                    self.format_and_eval_string(self.center_freq)

        if self.average_nb:
            self.driver.average_count_SA = \
                self.format_and_eval_string(self.average_nb)

        if self.resolution_bandwidth:
            self.driver.RBW = \
                self.format_and_eval_string(self.resolution_bandwidth)

        if self.video_bandwidth:
            self.driver.VBW_SA = \
                self.format_and_eval_string(self.video_bandwidth)

        sweep_modes = {'SA': 'Spectrum Analyzer',
                       'SPEC': 'Basic Spectrum Analyzer',
                       'WAV': 'Waveform'}

        PSA_config = 'Start freq' + self.driver.start_freq + \
                     'Stop freq' + self.driver.stop_freq + \
                     'Span freq' + self.driver.span_frequency + \
                     'Center freq' + self.driver.center_frequency + \
                     'Average number' + self.driver.average_count_SA + \
                     'Resolution bandwidth' + self.driver.RBW + \
                     'Video bandwidth' + self.driver.VBW_SA + \
                     'Number of points' + self.driver.sweep_points_SA + \
                     'Mode' + sweep_modes[self.mode]

        self.write_in_database('PSA_config', PSA_config)

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(PSAGetTrace, self).check(*args, **kwargs)

        if self.mode == 'Start/Stop':
            try:
                if self.start_freq:
                    toto = self.format_and_eval_string(self.start_freq)
                    if self.driver == 'AgilentPSA':
                        if (toto < 3) or (toto > 26500000000):
                            raise Exception('out_of_range')

            except Exception as e:
                test = False
                if e.args == 'out_of_range':
                    traceback[self.task_path + '/' + self.task_name +
                              '-start_freq'] = 'Start frequency {} out of ' + \
                        'range'.format(self.start_freq)
                else:
                    traceback[self.task_path + '/' + self.task_name +
                              '-start_freq'] = 'Failed to eval the start' + \
                        'formula {}'.format(self.start_freq)

            try:
                if self.stop_freq:
                    toto = self.format_and_eval_string(self.stop_freq)
                    if self.driver == 'AgilentPSA':
                        if (toto < 3) or (toto > 26500000000):
                            raise Exception('out_of_range')

            except Exception as e:
                test = False
                if e.args == 'out_of_range':
                    traceback[self.task_path + '/' + self.task_name +
                              '-stop_freq'] = 'Stop frequency {} out of ' + \
                        'range'.format(self.start_freq)
                else:
                    traceback[self.task_path + '/' + self.task_name +
                              '-stop_freq'] = 'Failed to eval the stop' + \
                        'formula {}'.format(self.stop_freq)
        else:
            try:
                if self.span_freq:
                    toto = self.format_and_eval_string(self.span_freq)
                    if self.driver == 'AgilentPSA':
                        if (toto < 0) or (toto > 26500000000):
                            raise Exception('out_of_range')

            except Exception as e:
                test = False
                if e.args == 'out_of_range':
                    traceback[self.task_path + '/' + self.task_name +
                              '-span_freq'] = 'Span frequency {} out of ' + \
                        'range'.format(self.span_freq)
                else:
                    traceback[self.task_path + '/' + self.task_name +
                              '-span_freq'] = 'Failed to eval the span' + \
                        'formula {}'.format(self.span_freq)

            try:
                if self.center_freq:
                    toto = self.format_and_eval_string(self.center_freq)
                    if self.driver == 'AgilentPSA':
                        if (toto < 3) or (toto > 26500000000):
                            raise Exception('out_of_range')

            except Exception as e:
                test = False
                if e.args == 'out_of_range':
                    traceback[self.task_path + '/' + self.task_name +
                              '-center_freq'] = 'Center frequency {} out of ' + \
                        'range'.format(self.center_freq)
                else:
                    traceback[self.task_path + '/' + self.task_name +
                              '-center_freq'] = 'Failed to eval the stop' + \
                        'formula {}'.format(self.center_freq)

        try:
            if self.average_nb:
                toto = self.format_and_eval_string(self.average_nb)
                if self.driver == 'AgilentPSA':
                    if (toto < 1) or (toto > 8192):
                        raise Exception('out_of_range')

        except Exception as e:
            test = False
            if e.args == 'out_of_range':
                traceback[self.task_path + '/' + self.task_name +
                          '-average_nb'] = 'Average number {} out of ' + \
                    'range'.format(self.average_nb)
            else:
                traceback[self.task_path + '/' + self.task_name +
                          '-average_nb'] = 'Failed to eval the average_nb' + \
                    'formula {}'.format(self.average_nb)

        try:
            if self.average_nb:
                toto = self.format_and_eval_string(self.resolution_bandwidth)
                if self.driver == 'AgilentPSA':
                    if (toto < 1) or (toto > 8000000):
                        raise Exception('out_of_range')

        except Exception as e:
            test = False
            if e.args == 'out_of_range':
                traceback[self.task_path + '/' + self.task_name +
                          '-resolution_bandwidth'] = 'Resolution BW number' + \
                    '{} out of range'.format(self.average_nb)
            else:
                traceback[self.task_path + '/' + self.task_name +
                          '-resolution_bandwidth'] = 'Failed to eval the ' + \
                    'resolution_bandwidth formula {}' + \
                    ''.format(self.resolution_bandwidth)

        try:
            if self.average_nb:
                toto = self.format_and_eval_string(self.video_bandwidth)
                if self.driver == 'AgilentPSA':
                    if (toto < 1) or (toto > 50000000):
                        raise Exception('out_of_range')

        except Exception as e:
            test = False
            if e.args == 'out_of_range':
                traceback[self.task_path + '/' + self.task_name +
                          '-video_bandwidth'] = 'Video BW number' + \
                    '{} out of range'.format(self.video_bandwidth)
            else:
                traceback[self.task_path + '/' + self.task_name +
                          '-video_bandwidth'] = 'Failed to eval the ' + \
                    'video_bandwidth formula {}' + \
                    ''.format(self.video_bandwidth)

        return test, traceback

KNOWN_PY_TASKS = [PSAGetTrace, PSASetParam]
