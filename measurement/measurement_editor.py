# -*- coding: utf-8 -*-

from traits.api import (HasTraits, Instance, Button, Any, Bool)
from traitsui.api import (View, HGroup, UItem, Handler,TreeEditor, Menu,
                          TreeNode, Action, Separator, Spring, error)
from traits.etsconfig.etsconfig import ETSConfig
if ETSConfig.toolkit == 'wx':
    from traitsui.wx.tree_editor\
        import (CutAction, CopyAction, PasteAction, DeleteAction,
                RenameAction)
else:
    from traitsui.qt4.tree_editor\
        import (CutAction, CopyAction, PasteAction, DeleteAction,
                RenameAction)

from inspect import cleandoc
import textwrap

from .task_management.tasks import (ComplexTask, SimpleTask, AbstractTask,
                                    RootTask)
from .task_management.template_task_saver import TemplateTaskSaver
from.task_management.task_builder import TaskBuilder

class MeasurementEditorHandler(Handler):
    """
    """
    model = Any #Instance(MeasurementEditor)

    def close(self, info, is_ok):
        """This method, called when the ui is going to be destroyed, save the
        task being edited as a template to be reoponed on the next start of the
        program
        """
        pass

    def append_task(self, info, task):
        """
        """
        editor = info.tree
        node, task, nid = editor._data
        new_task = task.create_child(ui = info.ui)
        if new_task is not None:
            editor._undoable_append( node, task, new_task, False )
            editor._tree.setCurrentItem(nid.child(nid.childCount() - 1))

    def add_before(self, info, task):
        """
        """
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
        saver = TemplateTaskSaver()
        saver.save_template(task)

    def object_new_button_changed(self, info):
        """
        """
        message = cleandoc("""The measurement you are editing is about to be
                            destroyed to create a new one. Press OK to confirm,
                            or Cancel to go back to editing and get a chance to
                            save it.""")

        result = error(message = textwrap.fill(message.replace('\n', ' '),80),
                  title = 'Old measurement suppression',
                  parent = info.ui.control)

        if result:
            info.object.new_root_task()
            editor = info.tree
            nid = editor._get_object_nid(info.object.root_task)
            editor._tree.setCurrentItem(nid.child(0))

    def object_save_button_changed(self, info):
        """
        """
        message = cleandoc("""You are going to save the whole measurement you
                            are editing as a template. If you want to save only
                            a part of it, use the contextual menu.""")

        result = error(message = textwrap.fill(message.replace('\n', ' '),80),
                  title = 'Saving measurement',
                  parent = info.ui.control)

        if result:
            saver = TemplateTaskSaver()
            saver.save_template(info.object.root_task)

    def object_load_button_changed(self, info):
        """
        """
        builder = TaskBuilder(creating_root = True)
        builder.task_manager.filter_visible = False
        builder.task_manager.selected_task_filter_name = 'Template'
        root_task = builder.build(parent = None, ui = info.ui)
        if root_task is not None:
            info.object.root_task = root_task

    def object_ok_button_changed(self, info):
        """
        """
        info.ui.dispose()

append_action = Action(name = 'Append task',
                    action = 'append_task')

add_before_action = Action(name = 'Add before',
                           action = 'add_before')

add_after_action = Action(name = 'Add after',
                          action = 'add_after')

save_action = Action(name = 'Save as template',
                     action = 'save_as_template')

class MeasurementEditor(HasTraits):
    """
    """
    root_task = Instance(RootTask)

    new_button = Button('New measure')
    save_button = Button('Save measure')
    load_button = Button('Load template')
    enqueue_button = Button('Enqueue measure')
    ok_button = Button('OK')
    cancel_button = Button('Cancel')

    is_new_meas = Bool(True)

    editor = TreeEditor(
                        nodes = [
                            TreeNode( node_for  = [ ComplexTask ],
                                      auto_open = True,
                                      children  = 'children_task',
                                      label     = 'task_name',
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
                                      label     = 'task_name',
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

    def new_root_task(self):
        """
        """
        self.root_task = RootTask(task_builder = TaskBuilder)

    def default_traits_view(self):
        return View(
                    UItem('root_task',
                          editor = self.editor,
                          id = 'tree',
                          resizable = False,
                          ),
                    HGroup(
                        UItem('new_button', defined_when = 'is_new_meas'),
                        UItem('save_button'),
                        UItem('load_button', defined_when = 'is_new_meas'),
                        Spring(),
                        UItem('enqueue_button', defined_when = 'is_new_meas'),
                        UItem('ok_button',
                              defined_when = 'not is_new_meas'),
                        ),
                    resizable = True,
                    handler = MeasurementEditorHandler(model = self),
                    title = 'Live edition of the measure',
                    )

