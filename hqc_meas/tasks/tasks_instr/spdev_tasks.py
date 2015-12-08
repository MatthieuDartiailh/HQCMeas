# -*- coding: utf-8 -*-
# =============================================================================
# module : spdev_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""

"""
from atom.api import (Unicode, set_default)
from traceback import format_exc
import numpy as np

from hqc_meas.tasks.api import InstrumentTask


class DemodSPTask(InstrumentTask):
    """ Get the raw or averaged quadratures of the signal.
        Can also get raw or averaged traces of the signal.
    """
    # Frequency of the signal sent to channel 1 in MHz
    freq_1 = Unicode('50').tag(pref=True)

    # Frequency of the signal sent to channel 2 in MHz
    freq_2 = Unicode('50').tag(pref=True)

    # Time during which to acquire data after a trigger (s).
    duration = Unicode('0').tag(pref=True)

    # Time to wait after a trigger before starting acquisition (s).
    delay = Unicode('0').tag(pref=True)

    # Number of records to acquire (one per trig)
    records_number = Unicode('1000').tag(pref=True)

    driver_list = ['ADQ14']

    task_database_entries = set_default({'Ch1_I': 1.0, 'Ch1_Q': 1.0,
                                         'Ch2_I': 1.0, 'Ch2_Q': 1.0})

    def check(self, *args, **kwargs):
        """Check that parameters make sense.

        """
        test, traceback = super(DemodSPTask, self).check(*args, **kwargs)

        locs = {}
        for n in ('freq_1', 'freq_2', 'duration', 'delay', 'records_number'):
            try:
                locs[n] = self.format_and_eval_string(getattr(self, n))
            except Exception:
                test = False
                msg = 'Failed to evaluate formaula for %s : %s.\n%s'
                traceback[self.path + '/' + self.task_name + '-' + n] = \
                    msg % (n, getattr(self, n), format_exc())

        if not test:
            return test, traceback

        p1 = locs['freq_1']*1e6*locs['duration']
        p2 = locs['freq_2']*1e6*locs['duration']
        if (not p1.is_integer() or not p2.is_integer()):
            test = False
            msg = ('The duration must be an integer times the period of the '
                   'demodulations.')
            traceback[self.path + '/' + self.task_name + '-' + n] = msg

        return test, traceback

    def perform(self):
        """Acquire a number of traces average them and compute the demodualted
        siganl for both channels.

        """
        if not self.driver:
            self.start_driver()

        if self.driver.owner != self.task_name:
            self.driver.owner = self.task_name

            self.driver.configure_board()

        records_number = self.format_and_eval_string(self.records_number)
        delay = self.format_and_eval_string(self.delay)
        duration = self.format_and_eval_string(self.duration)

        ch1, ch2 = self.driver.get_traces(duration, delay, records_number)

        f1 = self.format_and_eval_string(self.freq_1)
        phi1 = np.arange(0, 2*np.pi*f1*duration, 2e-9)
        c1 = np.cos(phi1)
        s1 = np.sin(phi1)
        self.write_in_database('Ch1_I', np.mean(ch1*c1))
        self.write_in_database('Ch1_Q', np.mean(ch1*s1))
        del phi1, c1, s1

        f2 = self.format_and_eval_string(self.freq_2)
        phi2 = np.arange(0, 2*np.pi*f2*duration, 2e-9)
        c2 = np.cos(phi2)
        s2 = np.sin(phi2)
        self.write_in_database('Ch2_I', np.mean(ch2*c2))
        self.write_in_database('Ch2_Q', np.mean(ch2*s2))

KNOWN_PY_TASKS = [DemodSPTask]
