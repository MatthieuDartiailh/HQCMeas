# -*- coding: utf-8 -*-
#==============================================================================
# module : building.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from enaml.widgets.api import FileDialogEx

from .config import IniConfigTask
from .templates import load_template


import enaml
with enaml.imports():
    from .builder_view import (TemplateSelectorView, BuilderView)


def build_task(manager, parent_ui=None):
    """
    """
    dialog = BuilderView(manager=manager)
    result = dialog.exec_()
    if result:
        task, view = dialog.model.task_config.build_task()

        return task, view
    else:
        return None, None


def build_root(manager, mode, config=None, parent_ui=None):
    """
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
        return IniConfigTask.build_task_from_config(manager, config)
