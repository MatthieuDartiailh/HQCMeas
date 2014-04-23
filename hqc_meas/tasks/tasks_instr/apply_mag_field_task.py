# -*- coding: utf-8 -*-
#==============================================================================
# module : pna_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""

"""

from atom.api import (Str, Float, Bool, set_default)
from inspect import cleandoc

from ..instr_task import InstrumentTask
from ..tools.task_decorator import (smooth_instr_crash)
from ..tools.database_string_formatter import format_and_eval_string


class ApplyMagFieldTask(InstrumentTask):
    """Use a supraconducting magnet to apply a magnetic field. Parallel task.

    """
    # Target magnetic field (dynamically evaluated)
    target_field = Str().tag(pref=True)

    # Rate at which to sweep the field.
    rate = Float().tag(pref=True)

    # Whether to stop the switch heater after setting the field.
    auto_stop_heater = Bool(True).tag(pref=True)

    task_database_entries = set_default({'Bfield': 0.01})
    driver_list = ['IPS12010']
    loopable = True

    def __init__(self, **kwargs):
        super(ApplyMagFieldTask, self).__init__(**kwargs)
        self.make_parallel('instr')

    @smooth_instr_crash
    def process(self, target_value=None):
        """
        """
        if not self.driver:
            self.start_driver()

        if (self.driver.owner != self.task_name or
                not self.driver.check_connection()):
            self.driver.owner = self.task_name
            self.driver.make_ready()

        if target_value is None:
            target_value = format_and_eval_string(self.target_field,
                                                  self.task_path,
                                                  self.task_database)
        self.driver.go_to_field(target_value, self.rate, self.auto_stop_heater)
        self.write_in_database('Bfield', target_value)

        return True

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(ApplyMagFieldTask, self).check(*args, **kwargs)
        if self.target_field:
            try:
                val = format_and_eval_string(self.target_field, self.task_path,
                                             self.task_database)
            except:
                test = False
                traceback[self.task_path + '/' + self.task_name + '-field'] = \
                    cleandoc('''Failed to eval the target field formula
                        {}'''.format(self.target_field))
            self.write_in_database('Bfield', val)
        return test, traceback

KNOWN_PY_TASKS = [ApplyMagFieldTask]
