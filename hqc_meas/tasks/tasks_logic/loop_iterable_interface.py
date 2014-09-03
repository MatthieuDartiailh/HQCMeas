# -*- coding: utf-8 -*-
# =============================================================================
# module : loop_task.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import Str
from collections import Iterable

from ..task_interface import TaskInterface


class IterableLoopInterface(TaskInterface):
    """ Common logic for all loop tasks.

    """
    #: Value at which to start the loop.
    iterable = Str('0.0').tag(pref=True)

    def check(self, *args, **kwargs):
        """ Check evaluation of all loop parameters.

        """
        test = True
        traceback = {}
        task = self.task
        try:
            iterable = task.format_and_eval_string(self.iterable)
        except Exception:
            test = False
            traceback[task.task_path + '/' + task.task_name] = \
                'Loop task did not success to compute  the iterable'
            return test, traceback

        if isinstance(iterable, Iterable):
            task.write_in_database('point_number', len(iterable))
            if 'value' in task.task_database_entries:
                task.write_in_database('value', iterable[0])
        else:
            test = False
            traceback[task.task_path + '/' + task.task_name] = \
                'The computed iterable is not iterable.'

        return test, traceback

    def perform(self):
        """
        """
        task = self.task
        iterable = task.format_and_eval_string(self.iterable)

        task.perform_loop(iterable)

INTERFACES = {'LoopTask': [IterableLoopInterface]}
