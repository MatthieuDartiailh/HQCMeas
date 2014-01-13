# -*- coding: utf-8 -*-
"""
"""

from atom.api import (Atom, Str, Bool, Unicode, observe)

from configobj import ConfigObj
from inspect import getdoc

from ...tasks import BaseTask, RootTask, KNOWN_PY_TASKS
from ...atom_util import Subclass

class AbstractConfigTask(Atom):
    """
    """

    task_name = Str('')
    task_class = Subclass(BaseTask)
    config_ready = Bool(False)

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

class IniConfigTask(AbstractConfigTask):
    """This class handle the
    """

    template_path = Unicode()
    template_doc = Str()
    template_content = Str()

    def __init__(self, *args, **kwargs):
        super(IniConfigTask, self).__init__(*args, **kwargs)
        doc_list = ConfigObj(self.template_path).initial_comment
        doc = ''
        for line in doc_list:
            doc += line.replace('#','')
        self.template_doc = doc

    @observe('task_name')
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
        if self.task_class == RootTask and\
                                    config['task_class'] != 'ComplexTask':
            built_task = RootTask()
            task = self._get_task(config['task_class'])(task_name =
                                                            config['task_name'])
            built_task.children.append(task)
        else:
            task = self.task_class(task_name = self.task_name)
            built_task = task

        parameters = self._prepare_parameters(config)

        task.update_members_from_preferences(**parameters)
        return built_task

    @classmethod
    def build_task_from_config(cls, config):
        """
        """
        built_task = RootTask(task_name = 'Root')
        parameters = cls._prepare_parameters(config)
        built_task.update_members_from_preferences(**parameters)
        return built_task

    @classmethod
    def _build_child(cls, section):
        """
        """
        task = cls._get_task(section['task_class'])(task_name =
                                                    section['task_name'])
        parameters = cls._prepare_parameters(section)
        task.update_members_from_preferences(**parameters)

        return task

    @classmethod
    def _prepare_parameters(cls, section):
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
                    parameters[key].append(cls._build_child(section[entry]))
                else:
                    parameters[key] = [cls._build_child(section[entry])]

        return parameters

    @staticmethod
    def _get_task(name):
        for task in KNOWN_PY_TASKS:
            if task.__name__ == name:
                return task

class PyConfigTask(AbstractConfigTask):
    """
    """

    task_doc = Str()

    def __init__(self, *args, **kwargs):
        super(PyConfigTask, self).__init__(*args, **kwargs)
        self.task_doc = getdoc(self.task_class).replace('\n',' ')

    @observe('task_name')
    def check_parameters(self, change):
        if self.task_name != '':
            self.config_ready = True
        else:
            self.config_ready = False

    def build_task(self):
        return self.task_class(task_name = self.task_name)