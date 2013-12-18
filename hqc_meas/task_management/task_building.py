# -*- coding: utf-8 -*-
"""
"""

from atom.api import (Atom, Instance, Dict, observe, Typed, Bool)
from configobj import ConfigObj
from enaml.widgets.api import FileDialog

from .config import AbstractConfigTask, IniConfigTask, SPECIAL_CONFIG
from .task_manager import TaskManager

import enaml
with enaml.imports():
    from builder_view import TemplateSelectorView

class TaskBuilder(Atom):
    """
    """
    # Task manager and task we will build (all facilities for selecting and
    # filtering tasks are hold by task manager)
    task_manager = Typed(TaskManager, ())

    # Custom task config can be specified for tasks, when such a task is
    # selected the program instantiate the correct task config from the
    # special config dict
    configurable_tasks = Dict(default = SPECIAL_CONFIG)
    task_config = Instance(AbstractConfigTask)
    
    ok_ready = Bool()

    def __init__(self, *args, **kwargs):
        super(TaskBuilder, self).__init__(*args, **kwargs)

    @observe('task_manager.selected_task_name')
    def _new_selected_task(self, change):
        """This method request the task corresponding to the user selection from
        the task manager.
        """
        self.ok_ready = False
        config = self.configurable_tasks
        new = self.task_manager.task
        if new.has_key('template_path'):
            self.task_config = IniConfigTask(
                                    template_path = new['template_path'],
                                    task_class = new['class'])
        else:
            #Look up the hierarchy of the selected task to get the appropriate
            #TaskConfig
            task_class = new['class']
            for t_class in type.mro(task_class):
                if t_class in config:
                    self.task_config = config[t_class](task_class = task_class)
                    break

    @observe('task_config.config_ready')
    def _config_complete(self, change):
        """
        """
        self.ok_ready = change['value']

import enaml
with enaml.imports():
    from .builder_view import BuilderView

def build_task(parent_ui = None):
    """
    """
    builder_model = TaskBuilder()
    builder_view = BuilderView(model = builder_model)
    result = builder_view.exec_()
    if result:
        task = builder_model.task_config.build_task()

        return task
    else:
        return None
        
def build_root(mode, parent_ui = None, config = None):
    """
    """
    if mode == 'from config':
        pass
    
    elif mode == 'from file':
        path = FileDialog(parent = parent_ui, mode = 'open_file',
                          filters = ['*.ini']).exec_()
        config = ConfigObj(path)
        
    elif mode == 'from template':
        manager = TaskManager(selected_task_filter_name = 'Template')
        view = TemplateSelectorView(parent = parent_ui, model = manager)
        result = view.exec_()
        if result:
            path = view.path
        config = ConfigObj(path)
            
    if config:
        return IniConfigTask.build_task_from_config(config)