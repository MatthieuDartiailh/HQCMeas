# -*- coding: utf-8 -*-
#==============================================================================
# module : formula_task.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from atom.api import (Str, ContainerList, Instance, Atom, Bool)

from ..base_tasks import SimpleTask
from ..tools.database_string_formatter import (format_and_eval_string)


class Formula(Atom):
    """
    """
    label = Str()
    formula = Str()


class FormulaTask(SimpleTask):
    """Compute values according to formulas. Any valid python expression can be
    evaluated and replacement to access to the database data can be used.
    """
    # List of formulas.
    formulas = ContainerList(Instance(Formula))

    # Flag indicating the state of the database.
    database_ready = Bool(False)

    def __init__(self, **kwargs):
        super(FormulaTask, self).__init__(**kwargs)
        self.make_wait()

    def process(self):
        """
        """
        for i, formula in enumerate(self.formulas):
            value = format_and_eval_string(formula.formula,
                                           self.task_path,
                                           self.task_database)
            self.write_in_database(formula.label, value)

    def check(self, *args, **kwargs):
        """
        """
        traceback = {}
        test = True
        for i, formula in enumerate(self.formulas):
            try:
                val = format_and_eval_string(formula.formula, self.task_path,
                                             self.task_database)
                self.write_in_database(formula.label, val)
            except:
                test = False
                name = self.task_path + '/' + self.task_name + str(-(i+1))
                traceback[name] =\
                    "Failed to eval the formula {}".format(formula.label)
        return test, traceback

    def register_in_database(self):
        """ Override handling formulas.

        """
        if not self.database_ready:
            self.database_ready = True
        self.task_database_entries = {f.label: 0.0 for f in self.formulas}
        super(FormulaTask, self).register_in_database()

    def register_preferences(self):
        """ Override handling formulas.

        """
        super(FormulaTask, self).register_preferences()
        self.task_preferences['formulas'] = \
            repr([(f.label, f.formula) for f in self.formulas])

    update_preferences_from_members = register_preferences

    def update_members_from_preferences(self, **parameters):
        """ Override handling formulas.

        """
        super(FormulaTask, self).update_members_from_preferences(**parameters)
        if 'formulas' in parameters:
            self.definitions = [Formula(label=f[0], formula=f[1])
                                for f in parameters['formulas']]

KNOWN_PY_TASKS = [FormulaTask]
