# -*- coding: utf-8 -*-
"""
"""
from traitsui.api import (View, Group, VGroup, UItem, Label, EnumEditor)

from .instr_task import InstrumentTask
from .tools.task_decorator import make_stoppable, make_wait, smooth_instr_crash

class MeasDcVoltageTask(InstrumentTask):
    """
    """
    driver_list = ['Agilent34410A']

    task_database_entries = ['voltage']

    task_view = View(
                    VGroup(
                        UItem('task_name', style = 'readonly'),
                        Group(
                            Label('Driver'), Label('Instr'),
                            UItem('selected_driver',
                                editor = EnumEditor(name = 'driver_list'),
                                width = 100),
                            UItem('selected_profile',
                                editor = EnumEditor(name = 'profile_list'),
                                width = 100),
                            columns = 2,
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

        value = self.driver.read_voltage_dc()
        print value
        self.write_in_database('voltage', value)