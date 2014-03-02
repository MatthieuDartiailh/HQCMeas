# -*- coding: utf-8 -*-
#==============================================================================
# module : building.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from enaml.widgets.api import FileDialogEx

from .config.api import IniConfigTask
from .templates import load_template


import enaml
with enaml.imports():
    from .builder_view import (TemplateSelectorView, BuilderView)


def build_task(manager, parent_ui=None):
    """ Open a dialog to include a task in a task hierarchy.

    Parameters:
    ----------
    manager : TaskManagerPlugin
        Instance of the current task manager plugin.

    parent_ui : optional
        Optional parent widget for the dialog.

    Returns:
    -------
    task : BaseTask
        Task selected by the user to be added to a hierarchy.

    """
    dialog = BuilderView(manager=manager, parent=parent_ui)
    result = dialog.exec_()
    if result:
        task = dialog.model.task_config.build_task()

        return task
    else:
        return None


def build_root(manager, mode, config=None, parent_ui=None):
    """ Create a new RootTask.

    Parameters
    ----------
    manager : TaskManagerPlugin
        Instance of the current task manager plugin.

    mode : {'from config', 'from template', 'from file'}
        Whether to use the given config, or look for one in templates or a
        file.

    config : configobj.Section
        Object holding the informations necessary to build the root task.

    parent_ui : optional
        Optional parent widget for the dialog.

    Returns:
    -------
    task : RootTask

    """
    if mode == 'from config':
        pass

    elif mode == 'from file':
        path = FileDialogEx.get_open_file_name(parent=parent_ui,
                                               name_filters=['*.ini'])
        config, _ = load_template(path)

    elif mode == 'from template':
        view = TemplateSelectorView(parent=parent_ui, manager=manager)
        result = view.exec_()
        if result:
            path = view.path
        config, _ = load_template(path)

    if config:
        return IniConfigTask(manager=manager).build_task_from_config(config)
