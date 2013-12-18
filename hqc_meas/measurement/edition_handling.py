# -*- coding: utf-8 -*-
#==============================================================================
# module : measurement_edition.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
This module defines the tools used to edit a measurement (ie a hierarchical
set of task).

:Contains:
    MeasurementEditorHandler : Handler for the editor. Takes care of saving
        measures
    MeasurementEditor : View used to edit a measurement.
    MeasurementBuilderHandler : Handler for the measurement builder. Add to the
        editor the possibilty to load templates or saved mesures.
    MeasurementBuilder : View used to build a measurement from scratch.
"""

from atom.api import Atom
from enaml.widgets.api import FileDialog
from enaml.stdlib.message_box import question

from inspect import cleandoc
import textwrap

from ..tasks import RootTask
from ..task_management.task_saving import save_task
from ..task_management.task_building import build_root

class EditorHandler(Atom):
    """Handler for a MeasurementEditor handling the users pressing buttons.

    Methods
    -------
    object_save_template_button_changed(info):
        Method used to save the whole measurement as a template.
    object_save_button_changed(info):
        Method used to save a measurement in a file chosen by the user.

    """
    def save_template_clicked(self, widget):
        """Method used to save the whole measurement as a template.
        """
        message = cleandoc("""You are going to save the whole measurement
                            you are editing as a template. If you want to
                            save only a part of it, use the contextual
                            menu.""")

        result = question(widget,
                          'Saving measurement',
                          textwrap.fill(message.replace('\n', ' '),80),
                          )

        if result is not None and result.action == 'accept':
            save_task(widget.meas.root_task, mode = 'template')

    def save_clicked(self, widget):
        """Method used to save a measurement in a file chosen bu the user.
        """
        full_path = FileDialog(mode = 'save_file',
                          filters = [u'*.ini']).exec_()
        if not full_path:
            return
            
        widget.meas.save_measure(full_path)
                
    def new_clicked(self, widget):
        """Method used to create a new blank measurement.
        """
        message = cleandoc("""The measurement you are editing is about to
                        be destroyed to create a new one. Press OK to
                        confirm, or Cancel to go back to editing and get a
                        chance to save it.""")
                        
        result = question(widget,
                          'Old measurement suppression',
                          textwrap.fill(message.replace('\n', ' '),80),
                          )
        if result is not None and result.action == 'accept':
            widget.meas.root_task = RootTask()

    def load_clicked(self, widget):
        """Method used to load a measurement saved in a file.
        """
        full_path = FileDialog(mode = 'open_file',
                          filters = [u'*.ini']).exec_()
        if not full_path:
            return
            
        widget.meas.load_measure(full_path)
        widget.selected = widget.meas.root_task

    def load_template_clicked(self, widget):
        """Method used to load a measurement saved as a template.
        """
        meas = build_root(mode = 'from template', parent_ui = widget)
        if meas:
            widget.meas = meas