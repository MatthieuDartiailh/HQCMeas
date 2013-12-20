# -*- coding: utf-8 -*-
"""
"""
from atom.api\
    import (Str, Instance, Bool, observe, set_default)

from numpy import linspace
from timeit import default_timer

from .tools.task_decorator import make_stoppable
from .tools.database_string_formatter import format_and_eval_string
from .base_tasks import (SimpleTask, ComplexTask)

class BaseLoopTask(ComplexTask):
    """
    """
    task_start = Str('0.0').tag(pref = True)
    task_stop = Str('1.0').tag(pref = True)
    task_step = Str('0.1').tag(pref = True)
    timing = Bool().tag(pref = True)
    task_database_entries = set_default({'point_number' : 11, 'index' : 1})

    def check(self, *args, **kwargs):
        """
        """
        test = True
        traceback = {}
        try:
            start = format_and_eval_string(self.task_start, self.task_path,
                                         self.task_database)
        except:
            test = False
            traceback[self.task_path + '/' + self.task_name + '-start'] = \
                'Loop task did not success to compute  the start value'
        try:
            stop = format_and_eval_string(self.task_stop, self.task_path,
                                         self.task_database)
        except:
            test = False
            traceback[self.task_path + '/' + self.task_name + '-stop'] = \
                'Loop task did not success to compute  the stop value'
        try:
            step = format_and_eval_string(self.task_step, self.task_path,
                                         self.task_database)
        except:
            test = False
            traceback[self.task_path + '/' + self.task_name + '-step'] = \
                'Loop task did not success to compute the step value'
        try:
            num = int(abs((stop - start)/step))+ 1
            self.write_in_database('point_number', num)
        except:
            test = False
            traceback[self.task_path + '/' + self.task_name + '-points'] = \
                'Loop task did not success to compute the point number'

        if self.timing:
            self.process_ = self.process_with_timing
        else:
            self.process_ = self.process_no_timing

        check = super(BaseLoopTask, self).check( *args, **kwargs)
        test = test and check[0]
        traceback.update(check[1])
        return test, traceback

    @observe('timing')
    def _on_timing_changed(self, change):
        """
        """
        if change['type'] == 'update':
            if change['value']:
                self.process_ = self.process_with_timing
                aux = self.task_database_entries.copy()
                aux['elapsed_time'] = 1.0
                self.task_database_entries = aux
            else:
                self.process_ = self.process_no_timing
                aux = self.task_database_entries.copy()
                aux.pop('elapsed_time')
                self.task_database_entries = aux


class SimpleLoopTask(BaseLoopTask):
    """Complex task which, at each iteration, call all its child tasks.
    """
    task_database_entries = set_default({'point_number' : 11, 'index' : 1,
                                         'value' : 0})

    @make_stoppable
    def process_no_timing(self):
        """
        """
        start = format_and_eval_string(self.task_start, self.task_path,
                                         self.task_database)
        stop = format_and_eval_string(self.task_stop, self.task_path,
                                         self.task_database)
        step = format_and_eval_string(self.task_step, self.task_path,
                                         self.task_database)
        num = int(round(abs(((stop - start)/step)))) + 1
        self.write_in_database('point_number', num)
        for i, value in enumerate(linspace(start, stop, num)):
            if self.root_task.should_stop.is_set():
                break
            self.write_in_database('index', i+1)
            self.write_in_database('value', value)
            for child in self.children_task:
                child.process_()

    @make_stoppable
    def process_with_timing(self):
        """
        """
        start = format_and_eval_string(self.task_start, self.task_path,
                                         self.task_database)
        stop = format_and_eval_string(self.task_stop, self.task_path,
                                         self.task_database)
        step = format_and_eval_string(self.task_step, self.task_path,
                                         self.task_database)
        num = int(round(abs(((stop - start)/step)))) + 1
        self.write_in_database('point_number', num)
        for i, value in enumerate(linspace(start, stop, num)):
            if self.root_task.should_stop.is_set():
                break
            self.write_in_database('index', i+1)
            self.write_in_database('value', value)
            tic = default_timer()
            for child in self.children_task:
                child.process_()
            self.write_in_database('elapsed_time', default_timer()-tic)

class LoopTask(BaseLoopTask):
    """Complex task which, at each iteration, performs a task with a different
    value and then call all its child tasks.
    """
    task = Instance(SimpleTask).tag(child = True)
    task_database_entries = set_default({'point_number' : 11})

    @make_stoppable
    def process_no_timing(self):
        """
        """
        start = format_and_eval_string(self.task_start, self.task_path,
                                         self.task_database)
        stop = format_and_eval_string(self.task_stop, self.task_path,
                                         self.task_database)
        step = format_and_eval_string(self.task_step, self.task_path,
                                         self.task_database)
        num = int(round(abs(((stop - start)/step)))) + 1
        self.write_in_database('point_number', num)
        for i, value in enumerate(linspace(start, stop, num)):
            if self.root_task.should_stop.is_set():
                break
            self.write_in_database('index', i+1)
            self.task.process_(value)
            for child in self.children_task:
                child.process_()

    @make_stoppable
    def process_with_timing(self):
        """
        """
        start = format_and_eval_string(self.task_start, self.task_path,
                                         self.task_database)
        stop = format_and_eval_string(self.task_stop, self.task_path,
                                         self.task_database)
        step = format_and_eval_string(self.task_step, self.task_path,
                                         self.task_database)
        num = int(round(abs(((stop - start)/step)))) + 1
        self.write_in_database('point_number', num)
        for i, value in enumerate(linspace(start, stop, num)):
            if self.root_task.should_stop.is_set():
                break
            self.write_in_database('index', i+1)
            tic = default_timer()
            self.task.process_(value)
            for child in self.children_task:
                child.process_()
            self.write_in_database('elapsed_time', default_timer()-tic)

    def walk(self, members, callables):
        """
        """
        answer = super(LoopTask, self).walk(members, callables)
        answer.insert(1, self._answer(self.task, members, callables))
        return answer