# -*- coding: utf-8 -*-

from traits.api\
    import (Float, Bool)
from traitsui.api\
     import (View, Group, UItem, Label, EnumEditor)

import time

from .instr_task import InstrumentTask
from .tools.task_decorator import make_stoppable, make_parallel

class DCVoltageTask(InstrumentTask):
    """
    """
    target_value = Float
    back_step = Float
    delay = Float(0.01)
    check_value = Bool(False)

    last_value = Float

    driver_list = ['Yokogawa']
    loopable =  True

    database_entries = ['voltage']

    task_view = View(
                    Group(Label('Instr'), Label('Target (V)'),
                          Label('Back step'), Label('Delay (s)'),
                          Label('Check voltage'),
                          UItem('selected_profile',
                                editor = EnumEditor(name = 'profile_list'),
                                width = 100),
                          UItem('target_value'), UItem('back_step'),
                          UItem('delay'), UItem('check_value', tooltip =\
                          'Should the program ask the instrument the value of\
                          the applied voltage each time it is about to set\
                          it'.replace('\n', ' ')),
                          columns = 5,
                          ),
                     )
    loop_view = View(
                    Group(Label('Instr'), Label('Back step (V)'),
                          Label('Delay (s)'), Label('Check voltage'),
                          UItem('selected_profile',
                                editor = EnumEditor(name = 'profile_list'),
                                width = 100),
                          UItem('back_step'), UItem('delay'),
                          UItem('check_value', tooltip =\
                          'Should the program ask the instrument the value of\
                          the applied voltage each time it is about to set\
                          it'.replace('\n', ' ')),
                          columns = 4,
                          ),
                     )

    @make_stoppable
    @make_parallel
    def process(self, target_value = None):
        """
        """
        if not self.driver:
            self.start_driver()
            if hasattr(self.driver, 'set_function'):
                self.driver.set_function('VOLT')

        if target_value is not None:
            value = target_value
        else:
            value = self.target_value

        if self.check_value:
            last_value = self.driver.get_voltage()
        elif self.last_value == None:
            last_value = self.driver.get_voltage()

        if last_value == value:
            return
        elif self.back_step == 0:
            self.driver.set_voltage(value)
        else:
            if (value - last_value)/self.back_step > 0:
                step = self.back_step
            else:
                step = -self.back_step

        while abs(value-last_value) > abs(step):
            last_value += step
            self.driver.set_voltage(last_value)
            time.sleep(self.delay)

        self.driver.set_voltage(value)
        self.last_value = value
