# -*- coding: utf-8 -*-
from traits.api import (Instance, on_trait_change)
from traitsui.api import (View, UItem, TextEditor, HGroup, Label,
                          InstanceEditor)

from ..task_manager import TaskManager
from .base_task_config import PyConfigTask, AbstractConfigTask
from .loopable_task_config import loopable_task_config

class LoopConfigTask(PyConfigTask):
    """
    """
    task_manager = Instance(TaskManager, ())
    task_config = Instance(AbstractConfigTask)
    config_view = View(
                    HGroup(
                        Label('Task name'),
                        UItem('task_name'),
                        ),
                    UItem('task_doc', style = 'readonly',
                          editor = TextEditor(multi_line = True),
                          resizable = True
                          ),
                    HGroup(
                        UItem('task_manager', style = 'custom',
                              editor = InstanceEditor(view = 'builder_view'),
                              ),
                        UItem('task_config', style = 'custom',
                              editor = InstanceEditor(view = 'config_view')),
                        show_border = True,
                        label = 'Loop task',
                        ),

                    )

    def __init__(self, *args, **kwargs):
        super(LoopConfigTask, self).__init__(*args, **kwargs)
        self.task_manager.selected_task_filter_name = 'Loopable'
        self.task_manager.filter_visible = False

    @on_trait_change('task_config:config_ready')
    def check_parameters(self):
        if self.task_name != '' and self.task_config is not None:
            if self.task_config.config_ready:
                self.config_ready = True
            else:
                self.config_ready = False
        else:
            self.config_ready = False

    def build_task(self):
        loopable_task = self.task_config.build_task()
        return self.task_class(task_name = self.task_name, task = loopable_task)

    @on_trait_change('task_manager:selected_task_name')
    def _new_task(self, new):
        task_class = self.task_manager.get_task()['class']
        for t_class in type.mro(task_class):
            if t_class in loopable_task_config:
                config_class = loopable_task_config[t_class]
                self.task_config = config_class(task_class = task_class,
                                                task_parent = self)
                break
