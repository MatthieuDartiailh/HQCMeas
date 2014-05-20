# -*- coding: utf-8 -*-
#==============================================================================
# module : formula_task.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from atom.api import (Tuple, ContainerList)

from ..base_tasks import SimpleTask
from ..tools.database_string_formatter import (format_and_eval_string)


class FormulaTask(SimpleTask):
    """Compute values according to formulas. Any valid python expression can be
    evaluated and replacement to access to the database data can be used.
    """
    # List of formulas.
    formulas = ContainerList(Tuple()).tag(pref=True)

    def __init__(self, **kwargs):
        super(FormulaTask, self).__init__(**kwargs)
        self.make_wait()

    def process(self):
        """
        """
        for i, formula in enumerate(self.formulas):
            value = format_and_eval_string(formula[1],
                                           self.task_path,
                                           self.task_database)
            self.write_in_database(formula[0], value)

        return True

    def check(self, *args, **kwargs):
        """
        """
        traceback = {}
        test = True
        for i, formula in enumerate(self.formulas):
            try:
                val = format_and_eval_string(formula[1], self.task_path,
                                             self.task_database)
                self.write_in_database(formula[0], val)
            except Exception:
                test = False
                name = self.task_path + '/' + self.task_name + str(-(i+1))
                traceback[name] =\
                    "Failed to eval the formula {}".format(formula[0])
        return test, traceback

    def _observe_formulas(self, change):
        """ Observer keeping the list of database entries up to date.

        """
        self.task_database_entries = {f[0]: 0.0 for f in change['value']}

KNOWN_PY_TASKS = [FormulaTask]
