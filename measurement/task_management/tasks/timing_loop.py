# -*- coding: utf-8 -*-
from timeit import default_timer
from numpy import linspace
from .base_tasks import LoopTask
from .tools.task_decorator import make_stoppable

class TimingLoopTask(LoopTask):
    """
    """
    task_database_entries = ['point_number', 'elapsed_time']

    @make_stoppable
    def process(self):
        """
        """
        num = int((self.task_stop - self.task_start)/self.task_step) + 1
        self.write_in_database('point_number', num)
        for value in linspace(self.task_start, self.task_stop, num):
            tic = default_timer()
            self.task.process(value)
            for child in self.children_task:
                child.process()
            self.write_in_database('elapsed_time', default_timer()-tic)