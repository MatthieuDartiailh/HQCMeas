# -*- coding: utf-8 -*-
# =============================================================================
# module : tasks/manager/config/loop_task_config.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import (Instance, Value, Str, Bool, observe)

from .base_task_config import PyConfigTask, AbstractConfigTask


class LoopConfigTask(PyConfigTask):
    """
    """
    # Whether or not to embed a subtask.
    use_subtask = Bool()

    # Embedded task
    subtask = Str()

    # Configurer for the subtask.
    config = Instance(AbstractConfigTask)

    # View of the configurer
    config_view = Value()

    @observe('config.config_ready', 'task_name', 'use_subtask')
    def check_parameters(self, change):
        if self.config and change['name'] == 'task_name':
            self.config.task_name = change['value']

        if self.task_name != '':
            if self.use_subtask:
                if self.config is not None:
                    if self.config.config_ready:
                        self.config_ready = True
                    else:
                        self.config_ready = False
                else:
                    self.config_ready = False
            else:
                self.config_ready = True
        else:
            self.config_ready = False

    def build_task(self):
        if self.use_subtask:
            loopable_task = self.config.build_task()
            return self.task_class(task_name=self.task_name,
                                   task=loopable_task)
        else:
            return self.task_class(task_name=self.task_name)

    def _observe_subtask(self, change):
        """ Observer getting the right config and config view for the subtask.

        """
        if change['value']:
            conf, view = self.manager.config_request(change['value'])
            self.config = conf
            self.config_view = view(model=conf, loop=True)
            self.config.task_name = self.task_name

    def _observe_use_subtask(self, change):
        if not change['value']:
            self.subtask = ''
            self.config = None
