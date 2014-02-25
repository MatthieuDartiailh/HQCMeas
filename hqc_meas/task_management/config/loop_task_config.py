# -*- coding: utf-8 -*-
from atom.api import (Instance, observe)

from ..task_manager import TaskManager
from .base_task_config import PyConfigTask, AbstractConfigTask
from .loopable_task_config import loopable_task_config


class LoopConfigTask(PyConfigTask):
    """
    """
    task_manager = Instance(TaskManager, ())
    task_config = Instance(AbstractConfigTask)

    def __init__(self, *args, **kwargs):
        super(LoopConfigTask, self).__init__(*args, **kwargs)
        self.task_manager.selected_task_filter_name = 'Loopable'
        first = sorted(self.task_manager.tasks.keys())[0]
        self.task_manager.selected_task_name = first

    @observe('task_config.config_ready', 'task_name')
    def check_parameters(self, change):
        if self.task_config and change['name'] == 'task_name':
            self.task_config.task_name = change['value']

        if self.task_name != '' and self.task_config is not None:
            if self.task_config.config_ready:
                self.config_ready = True
            else:
                self.config_ready = False
        else:
            self.config_ready = False
        print self.config_ready

    def build_task(self):
        loopable_task = self.task_config.build_task()
        return self.task_class(task_name=self.task_name, task=loopable_task)

    @observe('task_manager.selected_task_name')
    def _new_task(self, new):
        task_class = self.task_manager.task['class']
        for t_class in type.mro(task_class):
            if t_class in loopable_task_config:
                config_class = loopable_task_config[t_class]
                self.task_config = config_class(task_class=task_class,
                                                task_name=self.task_name)
                break
