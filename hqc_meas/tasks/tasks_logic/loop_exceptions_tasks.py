# -*- coding: utf-8 -*-
# =============================================================================
# module : loops_exceptions_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import (Str, set_default)

from ..base_tasks import SimpleTask
from .loop_task import LoopTask
from .loop_exceptions import BreakException, ContinueException


class BreakTask(SimpleTask):
    """ Task breaking out of a loop when a condition is met.

    See Python break statement documenttaion.

    """

    condition = Str().tag(pref=True)

    parallel = set_default({'forbidden': True})

    def check(self, *args, **kwargs):
        """

        """
        test = True
        traceback = {}
        # XXXX to extend later for support of other looping tasks.
        if not isinstance(self.parent_task, LoopTask):
            test = False
            mess = 'Incorrect parent type: {}, expected LoopTask'
            traceback[self.task_path + '/' + self.task_name + '-parent'] = \
                mess.format(self.parent_task.task_class)

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
            raise BreakException()


class ContinueTask(SimpleTask):
    """ Task jumping to next loop iteration a condition is met.

    See Python continue statement documenttaion.

    """

    condition = Str().tag(pref=True)

    parallel = set_default({'forbidden': True})

    def check(self, *args, **kwargs):
        """

        """
        test = True
        traceback = {}
        # XXXX to extend later for support of other looping tasks.
        if not isinstance(self.parent_task, LoopTask):
            test = False
            mess = 'Incorrect parent type: {}, expected LoopTask'
            traceback[self.task_path + '/' + self.task_name + '-parent'] = \
                mess.format(self.parent_task.task_class)

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
            raise ContinueException()

KNOWN_PY_TASKS = [BreakTask, ContinueTask]
