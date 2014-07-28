# -*- coding: utf-8 -*-
#==============================================================================
# module : formula_task.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from atom.api import (Tuple, ContainerList, set_default)

from ..base_tasks import SimpleTask


class FormulaTask(SimpleTask):
    """Compute values according to formulas. Any valid python expression can be
    evaluated and replacement to access to the database data can be used.
    """
    #: List of formulas.
    formulas = ContainerList(Tuple()).tag(pref=True)

    wait = set_default({'activated': True})  # Wait on all pools by default.

    def perform(self):
        """
        """
        for i, formula in enumerate(self.formulas):
            value = self.format_and_eval_string(formula[1])
            self.write_in_database(formula[0], value)

    def check(self, *args, **kwargs):
        """
        """
        traceback = {}
        test = True
        for i, formula in enumerate(self.formulas):
            try:
                val = self.format_and_eval_string(formula[1])
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
        self.task_database_entries = {f[0]: 1.0 for f in change['value']}

KNOWN_PY_TASKS = [FormulaTask]
