# -*- coding: utf-8 -*-
"""
"""
from traits.api import (HasTraits, Instance, Button, Any, Property)
from traitsui.api import (View, HGroup, UItem, Handler,TreeEditor, Menu,
                          TreeNode, Action, Separator, Spring, error, VGroup)
from traitsui.qt4.tree_editor\
    import (CutAction, CopyAction, PasteAction, DeleteAction,
            RenameAction)
from pyface.qt import QtGui

from configobj import ConfigObj
from inspect import cleandoc
import textwrap

from .task_management.tasks import (ComplexTask, SimpleTask, AbstractTask,
                                    RootTask)
from .task_management.template_task_saver import TemplateTaskSaver
from.task_management.task_builder import TaskBuilder
from.task_management.config.base_task_config import IniConfigTask

class MeasurementTreeViewHandler(Handler):
    """
    """
    model = Any #Instance(MeasurementTreeView)

    def append_task(self, info, task):
        """
        """
        if info.initialized:
            editor = info.tree
            node, task, nid = editor._data
            new_task = task.create_child(ui = info.ui)
            if new_task is not None:
                editor._undoable_append( node, task, new_task, False )
                editor._tree.setCurrentItem(nid.child(nid.childCount() - 1))

    def add_before(self, info, task):
        """
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
                editor._undoable_insert(parent_node, parent_task, index, new_task)
                editor._tree.setCurrentItem(parent_nid.child(index))

    def add_after(self, info, task):
        """
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
                editor._undoable_insert(parent_node, parent_task, index, new_task)
                editor._tree.setCurrentItem(parent_nid.child(index))

    def save_as_template(self, info, task):
        """
        """
        if info.initialized:
            saver = TemplateTaskSaver()
            saver.save_template(task)

append_action = Action(name = 'Append task',
                    action = 'append_task')

add_before_action = Action(name = 'Add before',
                           action = 'add_before')

add_after_action = Action(name = 'Add after',
                          action = 'add_after')

save_action = Action(name = 'Save as template',
                     action = 'save_as_template')

class MeasurementTreeView(HasTraits):
    """
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
                                                    RenameAction,
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
                                                    save_action,
                                                    DeleteAction,
                                                    Separator(),
                                                    RenameAction,
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
    """
    """
    def object_save_template_button_changed(self, info):
        """
        """
        if info.initialized:
            message = cleandoc("""You are going to save the whole measurement you
                                are editing as a template. If you want to save only
                                a part of it, use the contextual menu.""")

            result = error(message = textwrap.fill(message.replace('\n', ' '), 80),
                      title = 'Saving measurement',
                      parent = info.ui.control)

            if result:
                saver = TemplateTaskSaver()
                saver.save_template(info.object.root_task)

    def object_save_button_changed(self, info):
        """
        """
        if info.initialized:
            dlg = QtGui.QFileDialog(info.ui.control)
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
    """
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
        """
        """
        return self.measurement_view.root_task

    def _set_root_task(self, value):
        """
        """
        self.measurement_view.root_task = value

class MeasurementBuilderHandler(MeasurementEditorHandler):
    """
    """

    def close(self, info, is_ok):
        """This method, called when the ui is going to be destroyed, save the
        task being edited as a template to be reopened on the next start of the
        program
        """
        pass

    def object_new_button_changed(self, info):
        """
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
        """
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
        """
        """
        if info.initialized:
            builder = TaskBuilder(creating_root = True)
            builder.task_manager.filter_visible = False
            builder.task_manager.selected_task_filter_name = 'Template'
            root_task = builder.build(parent = None, ui = info.ui)
            if root_task is not None:
                info.object.root_task = root_task


class MeasurementBuilder(MeasurementEditor):
    """
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
        self.new_root_task()

    def new_root_task(self):
        """
        """
        self.root_task = RootTask(task_builder = TaskBuilder)