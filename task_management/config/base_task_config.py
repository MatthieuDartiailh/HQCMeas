# -*- coding: utf-8 -*-
"""
"""

from traits.api import (HasTraits, Type, Str, Instance, File, Button)
from traitsui.api import (View, UItem, TextEditor, Handler, CodeEditor, Item)

import os
from configobj import ConfigObj
from inspect import getdoc

from tasks import AbstractTask,
from task_builder import TaskBuilder

class AbstractConfigTask(HasTraits):
    """
    """

    task_builder = Instance(TaskBuilder)
    task_name = Str('')
    task_class = Type(AbstractTask)
    config_view = View

    def check_parameters(self):
        """This method check if enough parameters has been provided to build
        the task
        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractConfigTask. This method is called each time a trait is changed\
        to check if enough parameters has been provided to build the task.'
        raise NotImplementedError(err_str)

    def build_task(self):
        """This method use the user parameters to build the task object

         Returns
        -------
        task : instance(AbstractTask)
            task object
        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractConfigTask. This method is called when the user validate its\
        choices and that the task must be built.'
        raise NotImplementedError(err_str)

    def _anytrait_changed(self):
        self.check_parameters()

class IniConfigTaskHandler(Handler):
    """
    """

    def object_ini_edit_button_changed(self, info):
        """
        """
        model = info.object
        with open(model.ini_path) as ini_file:
            model.ini_content = ini_file.read()
        ui = model.edit_traits(view = 'edit_view', parent = info.ui.control)
        if ui.result:
            with open(model.ini_path, 'w') as ini_file:
                ini_file.write(model.ini_content)
        model.ini_doc = ConfigObj(model.ini_path).initial_comment


class IniConfigTask(AbstractConfigTask):
    """This class handle the
    """

    ini_path = File
    ini_doc = Str
    ini_content = Str
    ini_edit_button = Button('Edit')

    config_view = View(
                    Item('task_name'),
                    UItem('ini_doc', style = 'readonly',
                          editor = TextEditor(multiline = True)),
                    UItem('ini_edit_button'),
                    )

    edit_view = View(
                    UItem('ini_content', editor = CodeEditor()),
                    buttons = ['OK', 'Cancel'],
                    resizable = True,
                    kind = 'modal',
                    )

    def __init__(self, preference, *args, **kwargs):
        super(IniConfigTask, self).__init__(*args, **kwargs)
        self.ini_path = os.path.abspath(preference)
        self.ini_doc = ConfigObj(self.ini_path).initial_comment

    def check_parameters(self):
        if self.task_name is not '':
            self.task_builder.config_ready = True

    def build_task(self):
        #TODO write this awful method which must from an ini build a complex
        #task
        pass

class PyConfigTask(AbstractConfigTask):
    """
    """

    task_doc = Str

    config_view = View(
                    Item('task_name'),
                    UItem('task_doc', style = 'readonly',
                          editor = TextEditor(multiline = True)),
                    )


    def __init__(self, *args, **kwargs):
        super(PyConfigTask, self).__init__(*args, **kwargs)
        self.task_doc = getdoc(self.task_class)

    def check_parameters(self):
        if self.task_name is not '':
            self.task_builder.config_ready = True

    def build_task(self):
        return self.task_class(task_name = self.task_name)

class InstrConfigTask(PyConfigTask):
    """
    """
    pass

class LoopConfigTask(PyConfigTask):
    """
    """
    pass

