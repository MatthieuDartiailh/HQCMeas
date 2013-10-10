# -*- coding: utf-8 -*-
"""
"""
from traits.api import (Float, Bool, Any, Str)
from traitsui.api import (View, Group, VGroup, UItem, Label, EnumEditor,
                          LineCompleterEditor)

import time, logging
from inspect import cleandoc
from textwrap import fill

from .instr_task import InstrumentTask
from .tools.task_decorator import (make_stoppable, make_parallel,
                                   smooth_instr_crash)
from .tools.database_string_formatter import format_and_eval_string

class SetDCVoltageTask(InstrumentTask):
    """
    """
    target_value = Str(preference = True)
    back_step = Float(preference = True)
    delay = Float(0.01, preference = True)
    check_value = Bool(False, preference = True)
    use_parallel = Bool(True, preference = True)

    #Actually a Float but I don't want it to get initialised at 0
    last_value = Any

    driver_list = ['YokogawaGS200', 'Yokogawa7651']
    loopable =  True

    task_database_entries = {'voltage' : 1.0}

    loop_view = View(
                    Group(
                        Label('Driver'), Label('Instr'), Label('Back step (V)'),
                        Label('Delay (s)'), Label('Check voltage'),
                        Label('Parallelize'),
                        UItem('selected_driver',
                                editor = EnumEditor(name = 'driver_list'),
                                width = 100),
                        UItem('selected_profile',
                                editor = EnumEditor(name = 'profile_list'),
                                width = 100),
                        UItem('back_step'), UItem('delay'),
                        UItem('check_value', tooltip = fill(cleandoc(
                        '''Should the program ask the instrument the value of
                        the applied voltage each time it is about to set
                        it'''), 80)),
                        UItem('use_parallel'),
                        columns = 6,
                        ),
                     )

    def __init__(self, *args, **kwargs):
        super(SetDCVoltageTask, self).__init__(*args, **kwargs)
        self._define_task_view()

    @make_stoppable
    @make_parallel('use_parallel')
    @smooth_instr_crash
    def process(self, target_value = None):
        """
        """
        if not self.driver:
            self.start_driver()

        if self.driver.owner != self.task_name:
            self.driver.owner = self.task_name
            if self.driver.function != 'VOLT':
                log = logging.getLogger()
                log.fatal(cleandoc('''Instrument assigned to task {} is not
                            configured to output a voltage'''.format(
                                                        self.task_name)))
                self.root_task.task_stop.set()
                return

        if target_value is not None:
            value = target_value
        else:
            value = format_and_eval_string(self.target_value, self.task_path,
                                           self.task_database)

        if self.check_value:
            last_value = self.driver.voltage
        elif self.last_value == None:
            last_value = self.driver.voltage
        else:
            last_value = self.last_value

        if last_value == value:
            self.write_in_database('voltage', value)
            return
        elif self.back_step == 0:
            self.driver.voltage = value
            return
        else:
            if (value - last_value)/self.back_step > 0:
                step = self.back_step
            else:
                step = -self.back_step

        if abs(value-last_value) > abs(step):
            while True:
                last_value += step
                self.driver.voltage = last_value
                if abs(value-last_value) > abs(step):
                    time.sleep(self.delay)
                else:
                    break

        self.driver.voltage = value
        self.last_value = value
        self.write_in_database('voltage', value)

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(SetDCVoltageTask, self).check(*args,
                                                                    **kwargs)
        val = None
        if self.target_value:
            try:
                val = format_and_eval_string(self.target_value, self.task_path,
                                                   self.task_database)
            except:
                test = False
                traceback[self.task_path + '/' +self.task_name + '-volt'] = \
                    'Failed to eval the target value formula {}'.format(
                                                            self.target_value)
        self.write_in_database('voltage', val)
        return test, traceback

    def _list_database_entries(self):
        """
        """
        entries =  self.task_database.list_accessible_entries(self.task_path)
        return entries

    def _define_task_view(self):
        """
        """
        line_completer = LineCompleterEditor(
                             entries_updater = self._list_database_entries)
        view = View(
                    VGroup(
                        UItem('task_name', style = 'readonly'),
                        Group(
                            Label('Driver'), Label('Instr'),
                            Label('Target (V)'), Label('Back step'),
                            Label('Delay (s)'),Label('Check voltage'),
                            Label('Parallelize'),
                            UItem('selected_driver',
                                editor = EnumEditor(name = 'driver_list'),
                                width = 100),
                            UItem('selected_profile',
                                editor = EnumEditor(name = 'profile_list'),
                                width = 100),
                            UItem('target_value', editor = line_completer),
                            UItem('back_step'),
                            UItem('delay'), UItem('check_value', tooltip = \
                            fill(cleandoc(
                            '''Should the program ask the instrument the value
                            of the applied voltage each time it is about to set
                            it'''), 80)),
                            UItem('use_parallel'),
                            columns = 7,
                            show_border = True,
                            ),
                        ),
                     )

        self.trait_view('task_view', view)