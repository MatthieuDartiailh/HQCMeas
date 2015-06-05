# -*- coding: utf-8 -*-
# =============================================================================
# module : building.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
""" This module gather routines linked to building tasks.

Save for build_task_from_config, all this function are rather method of the
TaskManager and should not be called on their own. There are implemented here
only to simplify the manager.

"""
from enaml.widgets.api import FileDialogEx

from hqc_meas.tasks.api import RootTask
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


def build_task_from_config(config, dep_source, root=False):
    """ Rebuild a task hierarchy from a Section.

    Parameters
    ----------
    config : Section
        Section representing the task hierarchy.

    dep_source :
        Source of the build dependencies of the hierarchy. This can either
        be the instance of the TaskManager of a dict of dependencies.

    Returns
    -------
    task :
        Newly built task.

    """
    if not isinstance(dep_source, dict):
        core = dep_source.workbench.get_plugin('enaml.workbench.core')
        cmd = 'hqc_meas.dependencies.collect_build_dep_from_config'
        dep_source = core.invoke_command(cmd, {'config': config})
        if isinstance(dep_source, Exception):
            return None

    if root:
        return RootTask.build_from_config(config, dep_source)
    else:
        task_class = dep_source['tasks'][config.pop('task_class')]
        return task_class.build_from_config(config, dep_source)


def build_root(manager, mode, config=None, parent_ui=None, build_dep=None):
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

    build_dep : optional
        Optionnal dict containing the build dependencies.

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
        if build_dep is None:
            core = manager.workbench.get_plugin('enaml.workbench.core')
            cmd = 'hqc_meas.dependencies.collect_build_dep_from_config'
            build_dep = core.invoke_command(cmd, {'config': config})
        if isinstance(build_dep, Exception):
            return None

        config.pop('task_class')
        return RootTask.build_from_config(config, build_dep)
