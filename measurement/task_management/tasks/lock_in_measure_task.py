# -*- coding: utf-8 -*-
"""
"""
from traits.api import (Str, Float, on_trait_change)
from traitsui.api import (View, Group, VGroup, UItem, Label, EnumEditor)

from textwrap import fill
from time import sleep

from .instr_task import InstrumentTask
from .tools.task_decorator import make_stoppable, make_wait, smooth_instr_crash

class LockInMeasureTask(InstrumentTask):
    """
    """
    selected_mode = Str(preference = True)
    waiting_time = Float(preference = True)

    driver_list = ['SR7265-LI', 'SR7270-LI', 'SR830']

    task_database_entries = {'x' : 1.0}

    task_view = View(
                    VGroup(
                        UItem('task_name', style = 'readonly'),
                        Group(
                            Label('Driver'), Label('Instr'), Label('Mode'),
                            Label('Wait (s)'),
                            UItem('selected_driver',
                                editor = EnumEditor(name = 'driver_list'),
                                width = 100),
                            UItem('selected_profile',
                                editor = EnumEditor(name = 'profile_list'),
                                width = 100),
                            UItem('selected_mode',
                                editor = EnumEditor(values = ['X', 'Y', 'X&Y',
                                                              'Amp', 'Phase',
                                                              'Amp&Phase']),
                                width = 100),
                            UItem('waiting_time',
                                  tooltip = fill('Time to wait before querying\
                                          values from the lock-in', 80),
                                ),
                            columns = 4,
                            show_border = True,
                            ),
                        ),
                     )

    @make_stoppable
    @make_wait
    @smooth_instr_crash
    def process(self):
        """
        """
        if not self.driver:
            self.start_driver()

        sleep(self.waiting_time)

        if self.selected_mode == 'X':
            value = self.driver.read_x()
            self.write_in_database('x', value)
        elif self.selected_mode == 'Y':
            value = self.driver.read_y()
            self.write_in_database('y', value)
        elif self.selected_mode == 'X&Y':
            value_x, value_y = self.driver.read_xy()
            self.write_in_database('x', value_x)
            self.write_in_database('y', value_y)
        elif self.selected_mode == 'Amp':
            value = self.driver.read_amplitude()
            self.write_in_database('amplitude', value)
        elif self.selected_mode == 'Phase':
            value = self.driver.read_phase()
            self.write_in_database('phase', value)
        elif self.selected_mode == 'Amp&Phase':
            amplitude, phase = self.driver.read_amp_and_phase()
            self.write_in_database('amplitude', amplitude)
            self.write_in_database('phase', phase)

    @on_trait_change('selected_mode')
    def _update_database_entries(self, new):
        """
        """
        if self.selected_mode == 'X':
            self.task_database_entries = {'x' : 1.0}
        elif self.selected_mode == 'Y':
            self.task_database_entries = {'y' : 1.0}
        elif self.selected_mode == 'X&Y':
            self.task_database_entries = {'x' : 1.0, 'y' : 1.0}
        elif self.selected_mode == 'Amp':
            self.task_database_entries = {'amplitude' : 1.0}
        elif self.selected_mode == 'Phase':
            self.task_database_entries = {'phase' : 1.0}
        elif self.selected_mode == 'Amp&Phase':
            self.task_database_entries = {'amplitude' : 1.0, 'phase' : 1.0}