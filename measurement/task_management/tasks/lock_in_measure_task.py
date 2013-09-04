# -*- coding: utf-8 -*-
"""
"""
from traits.api import (Str)
from traitsui.api import (View, Group, VGroup, UItem, Label, EnumEditor)

from .instr_task import InstrumentTask
from .tools.task_decorator import make_stoppable, make_wait

class LockInMeasureTask(InstrumentTask):
    """
    """
    selected_mode = Str(preference = True)

    driver_list = ['SR7265-LI', 'SR7270-LI']

    task_database_entries = ['x','y','phase','amplitude']

    task_view = View(
                    VGroup(
                        UItem('task_name', style = 'readonly'),
                        Group(
                            Label('Driver'), Label('Instr'), Label('Mode'),
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
                            columns = 3,
                            show_border = True,
                            ),
                        ),
                     )

    @make_stoppable
    @make_wait
    def process(self):
        """
        """
        if not self.driver:
            self.start_driver()

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