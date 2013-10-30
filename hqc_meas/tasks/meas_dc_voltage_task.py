# -*- coding: utf-8 -*-
"""
"""
from traits.api import Float, Bool
from traitsui.api import (View, Group, VGroup, UItem, Label, EnumEditor)

from time import sleep

from .instr_task import InstrumentTask
from .tools.task_decorator import make_stoppable, make_wait, smooth_instr_crash

class MeasDCVoltageTask(InstrumentTask):
    """Measure a dc voltage. Wait for any parallel operation before execution
    and then wait the specified time before perfoming the measure.
    """
    wait_time = Float(preference = True)
    wait_parallel = Bool(True)

    driver_list = ['Agilent34410A', 'Keithley2000']

    task_database_entries = {'voltage' : 1.0}

    task_view = View(
                    VGroup(
                        UItem('task_name', style = 'readonly'),
                        Group(
                            Label('Driver'), Label('Instr'),Label('Wait (s)'),
                            Label('Wait parallel task'),
                            UItem('selected_driver',
                                editor = EnumEditor(name = 'driver_list'),
                                width = 100),
                            UItem('selected_profile',
                                editor = EnumEditor(name = 'profile_list'),
                                width = 100),
                            UItem('wait_time'),
                            UItem('wait_parallel'),
                            columns = 4,
                            show_border = True,
                            ),
                        ),
                     )

    @make_stoppable
    @make_wait('wait_parallel')
    @smooth_instr_crash
    def process(self):
        """
        """
        if not self.driver:
            self.start_driver()

        sleep(self.wait_time)

        value = self.driver.read_voltage_dc()
        self.write_in_database('voltage', value)