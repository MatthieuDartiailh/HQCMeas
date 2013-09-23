# -*- coding: utf-8 -*-
"""
"""
from traits.api import (Float, Bool, Any)
from traitsui.api import (View, Group, VGroup, UItem, Label, EnumEditor)

import time

from .instr_task import InstrumentTask
from .tools.task_decorator import (make_stoppable, make_parallel,
                                   smooth_instr_crash)

class SetDcVoltageTask(InstrumentTask):
    """
    """
    target_value = Float(preference = True)
    back_step = Float(preference = True)
    delay = Float(0.01, preference = True)
    check_value = Bool(False, preference = True)

    #Actually a Float but I don't want it to get initialised at 0
    last_value = Any

    driver_list = ['YokogawaGS200']
    loopable =  True

    task_database_entries = ['voltage']
    task_database_entries_default = [1]

    task_view = View(
                    VGroup(
                        UItem('task_name', style = 'readonly'),
                        Group(
                            Label('Driver'), Label('Instr'),
                            Label('Target (V)'), Label('Back step'),
                            Label('Delay (s)'),Label('Check voltage'),
                            UItem('selected_driver',
                                editor = EnumEditor(name = 'driver_list'),
                                width = 100),
                            UItem('selected_profile',
                                editor = EnumEditor(name = 'profile_list'),
                                width = 100),
                            UItem('target_value'), UItem('back_step'),
                            UItem('delay'), UItem('check_value', tooltip =\
                            'Should the program ask the instrument the value of\
                             the applied voltage each time it is about to set\
                             it'.replace('\n', ' ')),
                            columns = 6,
                            show_border = True,
                            ),
                        ),
                     )
    loop_view = View(
                    Group(
                        Label('Driver'), Label('Instr'), Label('Back step (V)'),
                        Label('Delay (s)'), Label('Check voltage'),
                        UItem('selected_driver',
                                editor = EnumEditor(name = 'driver_list'),
                                width = 100),
                        UItem('selected_profile',
                                editor = EnumEditor(name = 'profile_list'),
                                width = 100),
                        UItem('back_step'), UItem('delay'),
                        UItem('check_value', tooltip =\
                        'Should the program ask the instrument the value of\
                        the applied voltage each time it is about to set\
                        it'.replace('\n', ' ')),
                        columns = 5,
                        ),
                     )

    @make_stoppable
    @make_parallel
    @smooth_instr_crash
    def process(self, target_value = None):
        """
        """
        if not self.driver:
            self.start_driver()
            if hasattr(self.driver, 'function'):
                self.driver.function = 'VOLT'

        if target_value is not None:
            value = target_value
        else:
            value = self.target_value

        if self.check_value:
            last_value = self.driver.voltage
        elif self.last_value == None:
            last_value = self.driver.voltage

        if last_value == value:
            return
        elif self.back_step == 0:
            self.driver.voltage = value
        else:
            if (value - last_value)/self.back_step > 0:
                step = self.back_step
            else:
                step = -self.back_step

        while abs(value-last_value) > abs(step):
            last_value += step
            self.driver.voltage = last_value
            time.sleep(self.delay)

        self.driver.voltage = value
        self.last_value = value
        self.write_in_database('voltage', value)
