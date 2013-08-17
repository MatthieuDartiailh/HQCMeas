# -*- coding: utf-8 -*-
"""
"""

from traits.api import (HasTraits, Type, Str, Bool, File, Button, Instance)
from traitsui.api import (View, UItem, TextEditor, Handler, CodeEditor,
                          HGroup, Label)

from configobj import ConfigObj
from inspect import getdoc
import textwrap

from ...task_management import tasks
from ..tasks import AbstractTask, ComplexTask, RootTask
from ...instruments.instrument_manager import InstrumentManager

class AbstractConfigTask(HasTraits):
    """
    """

    task_name = Str('')
    task_class = Type(AbstractTask)
    parent_task = Instance(AbstractTask)
    config_ready = Bool(False)
    config_view = View

    def check_parameters(self):
        """This method check if enough parameters has been provided to build
        the task

        This methodd should fire the config_ready event each time it is called
        sending True if everything is allright, False otherwise.
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
    task_class = ComplexTask

    def object_template_edit_button_changed(self, info):
        """
        """
        model = info.object
        with open(model.template_path) as template_file:
            model.template_content = template_file.read()
        ui = model.edit_traits(view = 'edit_view', parent = info.ui.control)
        if ui.result:
            with open(model.template_path, 'w') as template_file:
                template_file.write(model.template_content)

        doc_list = ConfigObj(model.template_path).initial_comment
        doc = ''
        for line in doc_list:
            doc += line.replace('#','')
        model.template_doc = doc


class IniConfigTask(AbstractConfigTask):
    """This class handle the
    """

    template_path = File
    template_doc = Str
    template_content = Str
    template_edit_button = Button('Edit')

    config_view = View(
                    HGroup(
                        Label('Task name'),
                        UItem('task_name'),
                        ),
                    UItem('template_doc', style = 'readonly',
                          editor = TextEditor(multi_line = True)),
                    UItem('template_edit_button'),
                    handler = IniConfigTaskHandler(),
                    )

    edit_view = View(
                    UItem('template_content', editor = CodeEditor()),
                    buttons = ['OK', 'Cancel'],
                    resizable = True,
                    kind = 'modal',
                    title = 'Edit template',
                    )

    def __init__(self, *args, **kwargs):
        super(IniConfigTask, self).__init__(*args, **kwargs)
        doc_list = ConfigObj(self.template_path).initial_comment
        doc = ''
        for line in doc_list:
            doc += line.replace('#','')
        self.template_doc = doc
        if self.task_name == 'Root':
            root_view = View(
                            Label('Task description'),
                            UItem('template_doc', style = 'readonly',
                                  editor = TextEditor(multi_line = True)),
                            UItem('template_edit_button'),
                            handler = IniConfigTaskHandler(),
                            )
            self.trait_view('config_view', root_view)


    def check_parameters(self):
        if self.task_name is not '':
            self.config_ready = True
        else:
            self.config_ready = False

    def build_task(self):
        """
        """
        config = ConfigObj(self.template_path)
        #Handle the case of an attempt to make a root task of a task which is
        #not a ComplexTask. built_task will be returned but task will be the
        #object used for the following manipulations.
        if self.task_class == RootTask and config['task_class']!= 'ComplexTask':
            built_task = RootTask()
            task = getattr(tasks, config['task_class'])(task_name =
                                                            config['task_name'])
            built_task.children.append(task)
        else:
            task = self.task_class(task_name = self.task_name)
            built_task = task

        parameters = self._prepare_parameters(config)

        task.update_traits_from_preferences(**parameters)
        return built_task

    def _build_child(self, section):
        """
        """
        task = getattr(tasks, section['task_class'])(task_name =
                                                    section['task_name'])
        parameters = self._prepare_parameters(section)
        task.update_traits_from_preferences(**parameters)

        return task

    def _prepare_parameters(self, section):
        """

        Parameters:
            section : instance of Section
                Section describing the parameters which must be sent to the
                task

        Return:
            parameters : dict
                Dictionnary holding the parameters to be passed to a task
        """
        #First getting the non-task traits as string
        parameters = {}
        if section.scalars:
            for entry in section.scalars:
                if entry != 'task_class' and entry != 'task_name':
                    parameters[entry] = section[entry]

        #Second creating all the neccessary children
        if section.sections:
            for entry in section.sections:
                key = entry
                if any(i in entry for i in '0123456789'):
                    key = ''.join(c for c in entry if not c.isdigit())
                    if key.endswith('_'):
                        key = key[:-1]
                if parameters.has_key(key):
                    parameters[key].append(self._build_child(section[entry]))
                else:
                    parameters[key] = [self._build_child(section[entry])]

        return parameters


class PyConfigTask(AbstractConfigTask):
    """
    """

    task_doc = Str
    config_view = View(
                    HGroup(
                        Label('Task name'),
                        UItem('task_name'),
                        ),
                    UItem('task_doc', style = 'readonly',
                          editor = TextEditor(multi_line = True),
                          resizable = True),
                    )


    def __init__(self, *args, **kwargs):
        super(PyConfigTask, self).__init__(*args, **kwargs)
        doc = getdoc(self.task_class).replace('\n',' ')
        self.task_doc = doc

    def check_parameters(self):
        if self.task_name != '':
            self.config_ready = True
        else:
            self.config_ready = False

    def build_task(self):
        return self.task_class(task_name = self.task_name)

class InstrConfigTask(PyConfigTask):
    """
    """
    pass