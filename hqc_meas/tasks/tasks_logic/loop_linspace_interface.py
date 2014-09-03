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
            if 'value' in task.task_database_entries:
                task.write_in_database('value', start)
        except Exception as e:
            test = False
            mess = 'Loop task did not succeed to compute  the start value: {}'
            traceback[task.task_path + '/' + task.task_name + '-start'] = \
                mess.format(e)
        try:
            stop = task.format_and_eval_string(self.stop)
        except Exception as e:
            test = False
            mess = 'Loop task did not succeed to compute  the stop value: {}'
            traceback[task.task_path + '/' + task.task_name + '-stop'] = \
                mess.format(e)
        try:
            step = task.format_and_eval_string(self.step)
        except Exception as e:
            test = False
            mess = 'Loop task did not succeed to compute the step value: {}'
            traceback[task.task_path + '/' + task.task_name + '-step'] = \
                mess.format(e)

        if not test:
            return test, traceback

        try:
            num = int(abs((stop - start)/step)) + 1
            task.write_in_database('point_number', num)
        except Exception as e:
            test = False
            mess = 'Loop task did not succeed to compute the point number: {}'
            traceback[task.task_path + '/' + task.task_name + '-points'] = \
                mess.format(e)

        try:
            linspace(start, stop, num)
        except Exception:
            test = False
            mess = 'Loop task did not succeed to create a linspace: {}'
            traceback[task.task_path + '/' + task.task_name + '-linspace'] = \
                mess.format(e)

        return test, traceback

    def perform(self):
        """
        """
        task = self.task
        start = task.format_and_eval_string(self.start)
        stop = task.format_and_eval_string(self.stop)
        step = task.format_and_eval_string(self.step)
        num = int(round(abs(((stop - start)/step)))) + 1

        iterable = linspace(start, stop, num)
        task.perform_loop(iterable)

INTERFACES = {'LoopTask': [LinspaceLoopInterface]}
