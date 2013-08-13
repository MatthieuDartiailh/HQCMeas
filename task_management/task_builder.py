# -*- coding: utf-8 -*-
"""
"""

from traits.api import (HasTraits, Str, Instance, Type, Dict,
                        on_trait_change)
from traitsui.api import (View)

from tasks import AbstractTask
from task_config import AbstractConfigTask, special_config
from task_manager import TaskManager

class TaskBuilder(HasTraits):
    """
    """
    # Task manager and task we will build (all facilities for selecting and
    # filtering tasks are hold by task manager)
    task_manager = Instance(TaskManager, ())
    selected_task = Dict(Str)

    # Custom task config can be specified for tasks, when such a task is
    # selected the program instantiate the correct task config from the
    # special config dict
    configurable_tasks = Dict(Type(AbstractTask),
                              Type(AbstractConfigTask),
                              special_config)
    task_config = Instance(AbstractConfigTask)

    building_view = View()

    def __init__(self, *args, **kwargs):
        super(TaskBuilder, self).__init__(*args, **kwargs)
        #synchronise tasks and filters

    def build(self, parent, ui):
        """
        """
        #Here open the dialog allow user to select task and parameters
        #then return created child

    @on_trait_change('task_manager:selected_task_name')
    def _new_selected_task(self):
        """This method request the task corresponding to the user selection from
        the task manager.
        """
        self.selected_task = self.task_manager.get_task()

    @on_trait_change('selected_task')
    def _new_task(self, new):
        """This method handles the selection of a new task, selecting the right
        task config for display.
        """
        config = self.configurable_tasks
        task_class = new['class']
        if new.has_key('preference'):
            #TODO here retrun a INIconfigTask instance
            pass
        else:
            #Look up the hierarchy of the selected task to get the appropriate
            #TaskConfig
            for t_class in type.mro(task_class):
                if t_class in self.configurable_tasks:
                    return config[t_class](task_builder = self)
