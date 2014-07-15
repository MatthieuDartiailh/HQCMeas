# -*- coding: utf-8 -*-
# =============================================================================
# module : loop_task.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import Str
from numpy import linspace

from ..task_interface import TaskInterface


class LinspaceLoopInterface(TaskInterface):
    """ Common logic for all loop tasks.

    """
    #: Value at which to start the loop.
    start = Str('0.0').tag(pref=True)

    #: Value at which to stop the loop (included)
    stop = Str('1.0').tag(pref=True)

    #: Step between loop values.
    step = Str('0.1').tag(pref=True)

    def check(self, *args, **kwargs):
        """ Check evaluation of all loop parameters.

        """
        test = True
        traceback = {}
        task = self.task
        try:
            start = task.format_and_eval_string(self.start)
        except Exception:
            test = False
            traceback[task.task_path + '/' + task.task_name + '-start'] = \
                'Loop task did not success to compute  the start value'
        try:
            stop = task.format_and_eval_string(self.stop)
        except Exception:
            test = False
            traceback[task.task_path + '/' + task.task_name + '-stop'] = \
                'Loop task did not success to compute  the stop value'
        try:
            step = self.format_and_eval_string(self.step)
        except Exception:
            test = False
            traceback[task.task_path + '/' + task.task_name + '-step'] = \
                'Loop task did not success to compute the step value'

        if not test:
            return test, traceback

        try:
            num = int(abs((stop - start)/step)) + 1
            task.write_in_database('point_number', num)
        except Exception:
            test = False
            traceback[task.task_path + '/' + task.task_name + '-points'] = \
                'Loop task did not success to compute the point number'
        try:
            linspace(start, stop, num)
        except Exception:
            test = False
            traceback[task.task_path + '/' + task.task_name + '-linspace'] = \
                'Loop task did not success to create a linspace.'

        return test, traceback

    def perform(self):
        """
        """
        start = self.format_and_eval_string(self.task_start)
        stop = self.format_and_eval_string(self.task_stop)
        step = self.format_and_eval_string(self.task_step)
        num = int(round(abs(((stop - start)/step)))) + 1

        iterable = linspace(start, stop, num)
        self.task.loop_perform(iterable)

INTERFACES = {'LoopTask': [LinspaceLoopInterface]}
