# -*- coding: utf-8 -*-
# =============================================================================
# module : conditional_task.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import (Str)

from ..base_tasks import ComplexTask


class ConditionalTask(ComplexTask):
    """ Task breaking out of a loop when a condition is met.

    See Python break statement documenttaion.

    """
    logic_task = True

    condition = Str().tag(pref=True)

    def check(self, *args, **kwargs):
        """

        """
        test, traceback = super(ConditionalTask, self).check(*args, **kwargs)

        try:
            self.format_and_eval_string(self.condition)
        except Exception as e:
            test = False
            mess = 'Task did not succeed to compute the break condition: {}'
            traceback[self.task_path + '/' + self.task_name + '-cond'] = \
                mess.format(e)

        return test, traceback

    def perform(self):
        """

        """
        if self.format_and_eval_string(self.condition):
            for child in self.children_task:
                child.perform_(child)


KNOWN_PY_TASKS = [ConditionalTask]
