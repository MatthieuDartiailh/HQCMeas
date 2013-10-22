# -*- coding: utf-8 -*-
"""
"""

from traits.api import (HasTraits, Str, Instance, Type, Dict, Bool, Button,
                        on_trait_change)
from traitsui.api import (View, HGroup, VGroup, UItem, InstanceEditor, Handler)

from .tasks import AbstractTask, RootTask
from .config import AbstractConfigTask, IniConfigTask, SPECIAL_CONFIG
from .task_manager import TaskManager

class TaskBuilderHandler(Handler):
    """
    """

    def object_ok_button_changed(self, info):
        """
        """
        info.ui.result = True
        info.ui.dispose()

    def object_cancel_button_changed(self, info):
        """
        """
        info.ui.result = False
        info.ui.dispose()

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
                              SPECIAL_CONFIG)
    task_config = Instance(AbstractConfigTask)

    #For the time useless trait storing the parent of the new task
    parent = Instance(AbstractTask)

    creating_root = Bool(False)

    ok_button = Button('OK')
    ok_ready = Bool(False)
    cancel_button = Button('Cancel')

    building_view = View(
                        HGroup(
                            UItem('task_manager', style = 'custom',
                                 editor = InstanceEditor(view = 'builder_view'),
                                ),
                            UItem('task_config', style = 'custom',
                                  editor = InstanceEditor(view = 'config_view'),
                                ),
                            VGroup(
                                UItem('ok_button', enabled_when = 'ok_ready'),
                                UItem('cancel_button'),
                                )
                            ),
                            kind = 'livemodal',
                            resizable = True,
                            width = 500,
                            handler = TaskBuilderHandler(),
                            title = 'Select task',
                        )

    def __init__(self, *args, **kwargs):
        super(TaskBuilder, self).__init__(*args, **kwargs)

    def build(self, parent, ui):
        """
        """
        self.parent = parent

        build_ui = self.edit_traits(view = 'building_view',
                                        parent = ui.control)
        if build_ui.result:
            task = self.task_config.build_task()
#            if 'edit_view' in task.trait_views(View):
#                task.edit_traits(view = 'edit_view', kind = 'livemodal',
#                                 parent = ui.control)
#            else:
#                task.edit_traits(view = 'task_view', kind = 'livemodal',
#                                 parent = ui.control)

            if self.creating_root:
                task.task_builder = TaskBuilder

            return task
        else:
            return None

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
        self.ok_ready = False
        config = self.configurable_tasks
        if new.has_key('template_path'):
            if self.creating_root:
                self.task_config = IniConfigTask(task_parent = self.parent,
                                        template_path = new['template_path'],
                                        task_class = RootTask,
                                        task_name = 'Root')
                self.ok_ready = True
            else:
                self.task_config = IniConfigTask(task_parent = self.parent,
                                        template_path = new['template_path'],
                                        task_class = new['class'])
        else:
            #Look up the hierarchy of the selected task to get the appropriate
            #TaskConfig
            task_class = new['class']
            for t_class in type.mro(task_class):
                if t_class in config:
                    self.task_config = config[t_class](task_class = task_class,
                                         task_parent = self.parent)
                    break

    @on_trait_change('task_config:config_ready')
    def _config_complete(self, new):
        """
        """
        self.ok_ready = new
