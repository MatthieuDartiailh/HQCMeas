# -*- coding: utf-8 -*-
# =============================================================================
# module : lock_in_measure_task.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import (Enum, Float, set_default)

from time import sleep

from hqc_meas.tasks.api import InstrumentTask


class LockInMeasureTask(InstrumentTask):
    """Ask a lock-in to perform a measure.

    Wait for any parallel operationbefore execution.

    """
    # Value to retrieve.
    mode = Enum('X', 'Y', 'X&Y', 'Amp', 'Phase',
                'Amp&Phase').tag(pref=True)

    # Time to wait before performing the measurement.
    waiting_time = Float().tag(pref=True)

    driver_list = ['SR7265-LI', 'SR7270-LI', 'SR830']
    task_database_entries = set_default({'x': 1.0})

    wait = set_default({'activated': True, 'wait': ['instr']})

    def perform(self):
        """
        """
        if not self.driver:
            self.start_driver()

        sleep(self.waiting_time)

        if self.mode == 'X':
            value = self.driver.read_x()
            self.write_in_database('x', value)
        elif self.mode == 'Y':
            value = self.driver.read_y()
            self.write_in_database('y', value)
        elif self.mode == 'X&Y':
            value_x, value_y = self.driver.read_xy()
            self.write_in_database('x', value_x)
            self.write_in_database('y', value_y)
        elif self.mode == 'Amp':
            value = self.driver.read_amplitude()
            self.write_in_database('amplitude', value)
        elif self.mode == 'Phase':
            value = self.driver.read_phase()
            self.write_in_database('phase', value)
        elif self.mode == 'Amp&Phase':
            amplitude, phase = self.driver.read_amp_and_phase()
            self.write_in_database('amplitude', amplitude)
            self.write_in_database('phase', phase)

    def _observe_mode(self, change):
        """ Update the database entries acording to the mode.

        """
        new = change['value']
        if new == 'X':
            self.task_database_entries = {'x': 1.0}
        elif new == 'Y':
            self.task_database_entries = {'y': 1.0}
        elif new == 'X&Y':
            self.task_database_entries = {'x': 1.0, 'y': 1.0}
        elif new == 'Amp':
            self.task_database_entries = {'amplitude': 1.0}
        elif new == 'Phase':
            self.task_database_entries = {'phase': 1.0}
        elif new == 'Amp&Phase':
            self.task_database_entries = {'amplitude': 1.0, 'phase': 1.0}

KNOWN_PY_TASKS = [LockInMeasureTask]
