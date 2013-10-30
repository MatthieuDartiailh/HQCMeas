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
    MeasurementTreeViewHandler : Handler for the tree used to represent the
        measurement. Handles the contextual menu.
    MeasurementTreeView : Definition of the tree view used to represent the
        measurement.
    MeasurementEditorHandler : Handler for the editor. Takes care of saving
        measures
    MeasurementEditor : View used to edit a measurement.
    MeasurementBuilderHandler : Handler for the measurement builder. Add to the
        editor the possibilty to load templates or saved mesures.
    MeasurementBuilder : View used to build a measurement from scratch.
"""

from traits.api import (HasTraits, Instance, Button, Any, Property, Str)
from traitsui.api import (View, HGroup, UItem, Handler, TreeEditor, Menu,
                          TreeNode, Action, Separator, Spring, error, VGroup,
                          Item)
from traitsui.qt4.tree_editor\
    import (CutAction, CopyAction, PasteAction, DeleteAction)
from pyface.qt import QtGui

from configobj import ConfigObj
from inspect import cleandoc
import textwrap

from ..tasks import (ComplexTask, SimpleTask, AbstractTask,
                                    RootTask)
from ..task_management.template_task_saver import TemplateTaskSaver
from..task_management.task_builder import TaskBuilder
from..task_management.config.base_task_config import IniConfigTask

class TaskNameDialog(HasTraits):
    """
    """
    name = Str
    view = View(Item('name'), title = 'Enter the new name of the task',
                buttons = ['OK', 'Cancel'], kind = 'livemodal')

class MeasurementTreeViewHandler(Handler):
    """Handler for a MeasurementTreeView defining custom context menu actions.

    Attributes
    ----------
    model : instance(`MeasurementTreeView`)
        Convenience to access the `MeasurementTreeView` instance

    Methods
    -------
    append_task(info, task):
        Method allowing the user to append a task to the ones already attached
        to that node. Requires the node to accept children.
    add_before(info, task):
        Method allowing the user to add a task before the one he right clicked.
    add_after(info, task):
        Method allowing the user to add a task before the one he right clicked.
    save_as_template(info, task):
        Method used to create a template from a task. Requires the task to
        accept children.

    """
    model = Any #Instance(MeasurementTreeView)

    def append_task(self, info, task):
        """Method allowing the user to append a task to the ones already
        attached to that node. Requires the node to accept children.

        """
        if info.initialized:
            editor = info.tree
            node, task, nid = editor._data
            new_task = task.create_child(ui = info.ui)
            if new_task is not None:
                editor._undoable_append( node, task, new_task, False )
                editor._tree.setCurrentItem(nid.child(nid.childCount() - 1))

    def add_before(self, info, task):
        """Method allowing the user to add a task before the one he right
        clicked.

        """
        if info.initialized:
            editor = info.tree
            node, task, nid = editor._data
            parent_task = editor.get_parent(task)
            new_task = parent_task.create_child(ui = info.ui)
            if new_task is not None:
                index = editor._node_index(nid)[2]
                parent_node = editor.get_node(parent_task)
                parent_nid = editor._get_object_nid(parent_task)
                editor._undoable_insert(parent_node, parent_task, index,
                                        new_task)
                editor._tree.setCurrentItem(parent_nid.child(index))

    def add_after(self, info, task):
        """Method allowing the user to add a task before the one he right
        clicked.

        """
        if info.initialized:
            editor = info.tree
            node, task, nid = editor._data
            parent_task = editor.get_parent(task)
            new_task = parent_task.create_child(ui = info.ui)
            if new_task is not None:
                index = editor._node_index(nid)[2] + 1
                parent_node = editor.get_node(parent_task)
                parent_nid = editor._get_object_nid(parent_task)
                editor._undoable_insert(parent_node, parent_task, index,
                                        new_task)
                editor._tree.setCurrentItem(parent_nid.child(index))

    def rename(self, info, task):
        """Method allowing the user to rename a task.
        """
        if info.initialized:
            editor = info.tree
            node, task, nid = editor._data
            dialog = TaskNameDialog()
            ui = dialog.edit_traits(parent = info.ui.control)
            if ui.result:
                task.task_name = dialog.name

    def save_as_template(self, info, task):
        """Method used to create a template from a task. Requires the task to
        accept children.

        """
        if info.initialized:
            saver = TemplateTaskSaver()
            saver.save_template(task)

# Defining Actions calling Handler method for contextual menu of the view.
append_action = Action(name = 'Append task',
                    action = 'append_task')

add_before_action = Action(name = 'Add before',
                           action = 'add_before')

add_after_action = Action(name = 'Add after',
                          action = 'add_after')

save_action = Action(name = 'Save as template',
                     action = 'save_as_template')

rename_action = Action(name = 'Rename',
                     action = 'rename',
                     enabled_when = 'editor._is_renameable(object)' )

class MeasurementTreeView(HasTraits):
    """View representing a measurement as a tree.

    Attributes
    ----------
    root_task : instance(`RootTask`)
        Root_task representing the whole measurement being visualised.
    editor : instance(`TreeEditor`)
        Tree editor used to build the ui.

    Methods
    -------
    default_traits_view():
        Method building automatically the view for this object.

    """
    root_task = Instance(RootTask)

    editor = TreeEditor(
                        nodes = [
                            TreeNode( node_for  = [ ComplexTask ],
                                      auto_open = True,
                                      children  = 'children_task',
                                      label     = 'task_label',
                                      view_name = 'task_view',
                                      add       = [AbstractTask],
                                      menu      = Menu(Separator(),
                                                    append_action,
                                                    Separator(),
                                                    save_action,
                                                    DeleteAction,
                                                    Separator(),
                                                    rename_action,
                                                    Separator(),
                                                    CopyAction,
                                                    CutAction,
                                                    PasteAction)
                                    ),
                            TreeNode( node_for  = [ SimpleTask ],
                                      auto_open = True,
                                      children  = '',
                                      label     = 'task_label',
                                      view_name = 'task_view',
                                      menu      = Menu(Separator(),
                                                    add_before_action,
                                                    add_after_action,
                                                    Separator(),
#                                                    save_action,
                                                    DeleteAction,
                                                    Separator(),
                                                    rename_action,
                                                    Separator(),
                                                    CopyAction,
                                                    CutAction,
                                                    PasteAction)
                                    ),
                            ],
                        hide_root = False,
                        selected = 'selected_task',
                        )

    def default_traits_view(self):
        return View(
                    UItem('root_task',
                          editor = self.editor,
                          id = 'tree',
                          ),
                    resizable = True,
                    handler = MeasurementTreeViewHandler(model = self),
                    )

class MeasurementEditorHandler(Handler):
    """Handler for a MeasurementEditor handling the users pressing buttons.

    Methods
    -------
    object_save_template_button_changed(info):
        Method used to save the whole measurement as a template.
    object_save_button_changed(info):
        Method used to save a measurement in a file chosen bu the user.

    """
    def object_save_template_button_changed(self, info):
        """Method used to save the whole measurement as a template.
        """
        if info.initialized:
            message = cleandoc("""You are going to save the whole measurement
                                you are editing as a template. If you want to
                                save only a part of it, use the contextual
                                menu.""")

            result = error(message = textwrap.fill(message.replace('\n', ' '),
                                                   80),
                      title = 'Saving measurement',
                      parent = info.ui.control)

            if result:
                saver = TemplateTaskSaver()
                saver.save_template(info.object.root_task)

    def object_save_button_changed(self, info):
        """Method used to save a measurement in a file chosen bu the user.
        """
        if info.initialized:
            dlg = QtGui.QFileDialog(info.ui.control)
            dlg.setAcceptMode(QtGui.QFileDialog.AcceptSave)
            dlg.setNameFilter('*.ini')
            dlg.setDefaultSuffix('ini')
            if dlg.exec_() == QtGui.QDialog.Accepted:
                path = dlg.selectedFiles()[0]
                config = ConfigObj(path, indent_type = '    ')

                task = info.object.root_task
                task.update_preferences_from_traits()
                preferences = task.task_preferences

                config.merge(preferences)
                config.write()


class MeasurementEditor(HasTraits):
    """View used to edit a measurement. Allow saving.

    Attributes
    ----------
    measurement_view : instance(`MeasurementTreeView`)
        Instance of `MeasurementTreeView` used to visualize the measurement
        being edited.
    root_task : property
        Convenience to access the `root_task` object stored in `measurment_view`
    save_button : instance(`Button`)
        Button to save the measure (see `MeasurementEditorHandler`)
    save_template_button : instance(`Button`)
        Button to save the measure  as a template
        (see `MeasurementEditorHandler`)

    """
    measurement_view = Instance(MeasurementTreeView, ())
    root_task = Property
    save_button = Button('Save measure')
    save_template_button = Button('Save as template')

    traits_view = View(
                VGroup(
                    UItem('measurement_view', style = 'custom'),
                    HGroup(
                        UItem('save_button'),
                        UItem('save_template_button'),
                        ),
                    ),
                handler = MeasurementEditorHandler(),
                resizable = True,
                buttons = ['OK'],
                )

    def _get_root_task(self):
        """`root_task` getter method
        """
        return self.measurement_view.root_task

    def _set_root_task(self, value):
        """`root_task` setter method
        """
        self.measurement_view.root_task = value

class MeasurementBuilderHandler(MeasurementEditorHandler):
    """Handler for a MeasurementEditor handling the users pressing buttons.

    Methods
    -------
    object_new_button_changed(info):
        Method used to create a new blank measurement.
    object_load_button_changed(info):
        Method used to load a measurement saved in a file.
    object_load_template_button_changed(info):
        Method used to load a measurement saved as a template.

    """

    def close(self, info, is_ok):
        """This method, called when the ui is going to be destroyed, save the
        task being edited as a template to be reopened on the next start of the
        program. NOT IMPLEMENTED
        """
        pass

    def object_new_button_changed(self, info):
        """Method used to create a new blank measurement.
        """
        if info.initialized:
            message = cleandoc("""The measurement you are editing is about to
                            be destroyed to create a new one. Press OK to
                            confirm, or Cancel to go back to editing and get a
                            chance to save it.""")

            result = error(message = textwrap.fill(message.replace('\n', ' '), 80),
                      title = 'Old measurement suppression',
                      parent = info.ui.control)

            if result:
                info.object.new_root_task()

    def object_load_button_changed(self, info):
        """Method used to load a measurement saved in a file.
        """
        if info.initialized:
            dlg = QtGui.QFileDialog(info.ui.control)
            dlg.setNameFilter('*.ini')
            dlg.setFileMode(QtGui.QFileDialog.ExistingFile)
            if dlg.exec_() == QtGui.QDialog.Accepted:
                path = dlg.selectedFiles()[0]
                task_config = IniConfigTask(task_parent = None,
                                            template_path = path,
                                            task_class = RootTask,
                                            task_name = 'Root')
                task = task_config.build_task()
                task.task_builder = TaskBuilder
                info.object.root_task = task

    def object_load_template_button_changed(self, info):
        """Method used to load a measurement saved as a template.
        """
        if info.initialized:
            builder = TaskBuilder(creating_root = True)
            builder.task_manager.filter_visible = False
            builder.task_manager.selected_task_filter_name = 'Template'
            root_task = builder.build(parent = None, ui = info.ui)
            if root_task is not None:
                info.object.root_task = root_task


class MeasurementBuilder(MeasurementEditor):
    """View used to build a measurement. Allow saving, loading and creation.

    Attributes
    ----------
    measurement_view : instance(`MeasurementTreeView`)
        Instance of `MeasurementTreeView` used to visualize the measurement
        being edited.
    root_task : property
        Convenience to access the `root_task` object stored in `measurment_view`
    new_button : instance(`Button`)
        Button to create a new blanck measure (see `MeasurementBuilderHandler`)
    load_button : instance(`Button`)
        Button to load a measure stored in a file.
        (see `MeasurementBuilderHandler`)
    load_template_button : instance(`Button`)
        Button to load a measure stored in a template.
        (see `MeasurementBuilderHandler`)
    enqueue_button : instance(`Button`)
        Button to enqueue a measure.

    Methods
    -------
    new_root_task():
        Create a new blanck measure and make it the edited measure.

    """
    new_button = Button('New measure')
    load_button = Button('Load measure')
    load_template_button = Button('Load template')
    enqueue_button = Button('Enqueue measure')

    traits_view = View(
                    VGroup(
                        UItem('measurement_view', style = 'custom'),
                        HGroup(
                            UItem('new_button'),
                            UItem('save_button'),
                            UItem('save_template_button'),
                            UItem('load_button'),
                            UItem('load_template_button'),
                            Spring(),
                            UItem('enqueue_button'),
                            ),
                        ),
                    handler = MeasurementBuilderHandler()
                    )

    def __init__(self, *args, **kwargs):
        #Here I could reload an old measurement
        super(MeasurementBuilder, self).__init__(*args, **kwargs)
        self.new_root_task()

    def new_root_task(self):
        """Create a new blanck measure and make it the edited measure.
        """
        self.root_task = RootTask(task_builder = TaskBuilder)