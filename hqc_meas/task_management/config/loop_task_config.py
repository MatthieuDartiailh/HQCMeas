# -*- coding: utf-8 -*-
#==============================================================================
# module : loop_task_config.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from atom.api import (Instance, Value, Str, observe)

from ..manager_plugin import TaskManagerPlugin
from .base_task_config import PyConfigTask, AbstractConfigTask


class LoopConfigTask(PyConfigTask):
    """
    """
    # Task manager plugin.
    manager = Instance(TaskManagerPlugin, ())

    # Embedded task
    sub_task = Str()

    # Configurer for the subtask.
    config = Instance(AbstractConfigTask)

    # View of the configurer
    config_view = Value()

    @observe('config.config_ready', 'task_name')
    def check_parameters(self, change):
        if self.config and change['name'] == 'task_name':
            self.config.task_name = change['value']

        if self.task_name != '' and self.config is not None:
            if self.config.config_ready:
                self.config_ready = True
            else:
                self.config_ready = False
        else:
            self.config_ready = False

    def build_task(self):
        loopable_task = self.config.build_task()
        return self.task_class(task_name=self.task_name, task=loopable_task)

    def _observe_subtask(self, change):
        """ Observer getting the right config and config view for the subtask.

        """
        conf, view = self.manager.config_request(change['value'])
        self.config = conf
        self.config_view = view(model=conf, loop=True)
