# -*- coding: utf-8 -*-
# =============================================================================
# module : apply_mag_field_task.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""

"""
from atom.api import (Str, Int, set_default, Enum)
from inspect import cleandoc
import numpy as np

from hqc_meas.tasks.api import InstrumentTask


class GetPSATrace(InstrumentTask):
    """Get the trace displayed on the Power Spectrum Analyzer

    """
    trace = Int(1).tag(pref=True)

#    center_freq = Str().tag(pref=True)
#
#    span_freq = Str().tag(pref=True)
#
#    points = Str().tag(pref=True)
#
#    sweep_type = Enum('Spectrum Analyzer', 'Basic Spectrum Analyzer',
#                                              'Waveform').tag(pref=True)
#
#    resolution_bandwidth = Str().tag(pref=True)
#
#    video_bandwidth = Str().tag(pref=True)

    driver_list = ['AgilentPSA']
    task_database_entries = set_default({'trace_data': np.array([0])})
    #This initialization needs to change into a 2D array

    def perform(self):
        """
        """
        if not self.driver:
            self.start_driver()

        if self.driver.owner != self.task_name:
            self.driver.owner = self.task_name

#        center_freq = self.format_and_eval_string(self.center_freq)
#        span_freq = self.format_and_eval_string(self.span_freq)
#        points = self.format_and_eval_string(self.points)
#        resolution_bandwidth = \
#                        self.format_and_eval_string(self.resolution_bandwidth)
#        video_bandwidth = self.format_and_eval_string(self.video_bandwidth)
#        self.driver.span_frequency=span_freq
#        self.driver.center_frequency=center_freq
#        self.driver.RBW=resolution_bandwidth
#        self.driver.VBW_SA=video_bandwidth
#        self.driver.sweep_points_SA=points
#
        self.write_in_database('trace_data', self.driver.read_data(self.trace))


    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(GetPSATrace, self).check(*args, **kwargs)

    if self.trace>4 or self.trace<1:
        test = False
        traceback[self.task_path + '/' + self.task_name + '-get_trace'] = \
                    cleandoc('''Trace number {} is not valid
                        '''.format(self.trace))

        return test, traceback



KNOWN_PY_TASKS = [GetPSATrace]