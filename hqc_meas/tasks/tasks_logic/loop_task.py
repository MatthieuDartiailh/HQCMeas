# -*- coding: utf-8 -*-
# =============================================================================
# module : loop_task.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import (Instance, Bool, set_default)

from timeit import default_timer
from time import sleep

from ..base_tasks import (SimpleTask, ComplexTask)
from ..task_interface import InterfaceableTaskMixin
from .loop_exceptions import BreakException, ContinueException


class LoopTask(InterfaceableTaskMixin, ComplexTask):
    """ Complex task which, at each iteration, call all its child tasks.

    """
    # --- Public API ----------------------------------------------------------

    #: Flag indicating whether or not to time the loop.
    timing = Bool().tag(pref=True)

    #: Task to call before other child tasks with current loop value. This task
    #: is simply a convenience and can be set to None.
    task = Instance(SimpleTask).tag(child=True)

    task_database_entries = set_default({'point_number': 11, 'index': 1,
                                         'value': 0})

    def perform_loop(self, iterable):
        """ Perform the loop on the iterable calling all child tasks at each
        iteration.

        Parameters
        ----------
        iterable : iterable
            Iterable on which the loop should be performed.

        """
        if self.timing:
            if self.task:
                self._perform_loop_timing_task(iterable)
            else:
                self._perform_loop_timing(iterable)
        else:
            if self.task:
                self._perform_loop_task(iterable)
            else:
                self._perform_loop(iterable)

    # --- Private API ---------------------------------------------------------

    def _perform_loop(self, iterable):
        """

        """
        self.write_in_database('point_number', len(iterable))

        stop_flag = self.root_task.should_stop
        pause_flag = self.root_task.should_pause
        children = self._gather_children_task()
        for i, value in iterable:
            if stop_flag.is_set():
                break
            while pause_flag.is_set():
                sleep(0.05)
                if stop_flag.is_set():
                    return
            self.write_in_database('index', i+1)
            self.write_in_database('value', value)
            try:
                for child in children:
                    child.perform_(child)
            except BreakException:
                break
            except ContinueException:
                continue

    def _perform_loop_task(self, iterable):
        """

        """
        self.write_in_database('point_number', len(iterable))

        stop_flag = self.root_task.should_stop
        pause_flag = self.root_task.should_pause
        children = self._gather_children_task()
        for i, value in iterable:
            if stop_flag.is_set():
                break
            while pause_flag.is_set():
                sleep(0.05)
                if stop_flag.is_set():
                    return
            self.write_in_database('index', i+1)
            self.task.perform_(self.task, value)
            try:
                for child in children:
                    child.perform_(child)
            except BreakException:
                break
            except ContinueException:
                continue

    def _perform_loop_timing(self, iterable):
        """

        """
        self.write_in_database('point_number', len(iterable))

        stop_flag = self.root_task.should_stop
        pause_flag = self.root_task.should_pause
        children = self._gather_children_task()
        for i, value in iterable:
            if stop_flag.is_set():
                break
            while pause_flag.is_set():
                sleep(0.05)
                if stop_flag.is_set():
                    return
            self.write_in_database('index', i+1)
            self.write_in_database('value', value)
            tic = default_timer()
            try:
                for child in children:
                    child.perform_(child)
            except BreakException:
                break
            except ContinueException:
                continue
            self.write_in_database('elapsed_time', default_timer()-tic)

    def _perform_loop_timing_task(self, iterable):
        """

        """
        self.write_in_database('point_number', len(iterable))

        stop_flag = self.root_task.should_stop
        pause_flag = self.root_task.should_pause
        children = self._gather_children_task()
        for i, value in iterable:
            if stop_flag.is_set():
                break
            while pause_flag.is_set():
                sleep(0.05)
                if stop_flag.is_set():
                    return
            self.write_in_database('index', i+1)
            tic = default_timer()
            try:
                for child in children:
                    child.perform_(child)
            except BreakException:
                break
            except ContinueException:
                continue
            self.write_in_database('elapsed_time', default_timer()-tic)

    def _observe_task(self, change):
        """ Keep the database entries in sync with the task member.

        """
        if self.has_root:
            c_type = change['type']
            if 'oldvalue' in change and change['oldvalue']:
                self._child_removed(change['oldvalue'])

            if change['value'] and c_type != 'delete':
                self._child_added(change['value'])
                aux = self.task_database_entries.copy()
                if 'value' in aux:
                    del aux['value']
                self.task_database_entries = aux

            else:
                if c_type == 'delete':
                    self._child_removed(change['value'])
                aux = self.task_database_entries.copy()
                aux['value'] = 1.0
                self.task_database_entries = aux

    def _observe_timing(self, change):
        """ Keep the database entries in sync with the timing flag.

        """
        if change['value']:
            aux = self.task_database_entries.copy()
            aux['elapsed_time'] = 1.0
            self.task_database_entries = aux
        else:
            aux = self.task_database_entries.copy()
            if 'elapsed_time' in aux:
                del aux['elapsed_time']
            self.task_database_entries = aux

KNOWN_PY_TASKS = [LoopTask]
