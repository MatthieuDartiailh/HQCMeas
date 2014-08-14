# -*- coding: utf-8 -*-
#==============================================================================
# module : saving.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
import os.path
from enaml.widgets.api import FileDialogEx
import enaml
with enaml.imports():
    from .save_views import (TemplateTaskSaver, TemplateSaverDialog,
                             ScintillaDialog)

from .templates import save_template


def save_task(manager, task, mode, parent_ui=None):
    """ Save a task in an .ini file.

    Parameters
    ----------
    manager : TaskManagerPlugin
        Current task manager instance.

    task : BaseTask
        Task to save.

    mode : {'config', 'template', 'file'}
        Should the task be returned as a dict (config), saved as a,
        template, saved in a custom file.
    parent_ui : optional
        Optional widget to use as a parent for the dialogs.

    Returns:
    -------
    config or None:
        A dict is returned if the mode is 'config'.

    """
    full_path = u''
    if mode == 'template':
        saver = TemplateTaskSaver(manager=manager)
        saver_dialog = TemplateSaverDialog(parent=parent_ui, model=saver)

        if saver_dialog.exec_():
            if saver.template_filename.endswith('.ini'):
                full_path = os.path.join(saver.template_folder,
                                         saver.template_filename)
            else:
                full_path = os.path.join(saver.template_folder,
                                         saver.template_filename + '.ini')
        else:
            return

    elif mode == 'file':
        full_path = FileDialogEx(mode='save_file',
                                 filters=[u'*.ini']).exec_()
        if not full_path:
            return

    task.update_preferences_from_members()
    preferences = task.task_preferences

    if mode == 'config':
        return preferences

    else:
        doc = ''
        if mode == 'template':
            doc = saver.template_doc

        save_template(full_path, preferences.dict(), doc)

        if mode == 'template':
            if saver.show_result:
                with open(full_path) as f:
                    t = '\n'.join(f.readlines())
                    ScintillaDialog(parent=parent_ui, text=t).exec_()
