# -*- coding: utf-8 -*-
#==============================================================================
# module : pna_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""

"""

from traits.api import (Str, Float, Bool)
from traitsui.api import (View, Group, UItem, Label, EnumEditor,
                          LineCompleterEditor)

from inspect import cleandoc
from textwrap import fill

from .instr_task import InstrumentTask
from .tools.task_decorator import (make_stoppable, smooth_instr_crash,
                                   make_parallel)
from .tools.database_string_formatter import format_and_eval_string

class ApplyMagFieldTask(InstrumentTask):
    """
    """
    loopable = True

    target_field = Str(preference = True)
    rate = Float(preference = True)
    auto_stop_heater = Bool(True, preference = True)

    task_database_entries = ['Bfield']
    task_database_entries_default = [0.01]
    driver_list = ['IPS12010']

    loop_view = View(
                    UItem('task_name', style = 'readonly'),
                    Group(
                    Label('Driver'), Label('Instr'),
                    Label('Sweep rate (T/min)'),
                    Label('Auto stop heater'),
                    UItem('selected_driver',
                        editor = EnumEditor(name = 'driver_list'),
                        width = 100),
                    UItem('selected_profile',
                        editor = EnumEditor(name = 'profile_list'),
                        width = 100),
                    UItem('rate'),
                    UItem('auto_stop_heater',
                          tooltip = fill(cleandoc('''Check to enable the
                              automatic switch off of the switch heater after
                              each new value'''),80),
                        ),
                    columns = 4,
                    show_border = True,
                    ),
                )

    def __init__(self, *args, **kwargs):
        super(ApplyMagFieldTask, self).__init__(*args, **kwargs)
        self._define_task_view()

    @make_stoppable
    @make_parallel
    @smooth_instr_crash
    def process(self, target_value = None):
        """
        """
        if not self.driver:
            self.start_driver()

        if (self.driver.owner != self.task_name or
                            not self.driver.check_connection()):
            self.driver.owner = self.task_name
            self.driver.make_ready()

        if not target_value:
            target_value = format_and_eval_string(self.target_field,
                                                     self.task_path,
                                                     self.task_database)
        self.driver.go_to_field(target_value, self.rate, self.auto_stop_heater)
        self.write_in_database('Bfield', target_value)

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(ApplyMagFieldTask, self).check(*args,
                                                                     **kwargs)
        try:
            val = format_and_eval_string(self.target_field, self.task_path,
                                               self.task_database)
        except:
            test = False
            traceback[self.task_path + '/' +self.task_name] = \
                'Failed to eval the target field formula {}'.format(
                                                            self.target_value)
        self.write_in_database('Bfield', val)
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
                    Group(
                    Label('Driver'), Label('Instr'),
                    Label('Target field (T)'), Label('Sweep rate (T/min)'),
                    Label('Auto stop heater'),
                    UItem('selected_driver',
                        editor = EnumEditor(name = 'driver_list'),
                        width = 100),
                    UItem('selected_profile',
                        editor = EnumEditor(name = 'profile_list'),
                        width = 100),
                    UItem('target_field', editor = line_completer),
                    UItem('rate'),
                    UItem('auto_stop_heater',
                          tooltip = fill(cleandoc('''Check to enable the
                              automatic switch off of the switch heater after
                              each new value'''),80),
                        ),
                    columns = 5,
                    ),
                )
        self.trait_view('task_view', view)