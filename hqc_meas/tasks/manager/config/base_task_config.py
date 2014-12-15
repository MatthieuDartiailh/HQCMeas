# -*- coding: utf-8 -*-
# =============================================================================
# module : tasks/manager/config/base_task_config.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
""" Standard task configurers.

:Contains:
    AbstractConfigTask
    PyConfigTask
    IniConfigTask

"""

from atom.api import (Atom, Str, Bool, Unicode, Subclass, ForwardTyped,
                      observe)

from inspect import getdoc, cleandoc

from hqc_meas.tasks.api import BaseTask
from ..templates import load_template
from ..building import build_task_from_config
import random
import os


# Circular import protection
def task_manager():
    from ..plugin import TaskManagerPlugin
    return TaskManagerPlugin


class AbstractConfigTask(Atom):
    """ Base class for task configurer.

    """
    # Task manager, necessary to retrieve task implementations.
    manager = ForwardTyped(task_manager)

    # Name of the task to create.
    task_name = Str('')

    # Class of the task to create.
    task_class = Subclass(BaseTask)

    # Bool indicating if the build can be done.
    config_ready = Bool(False)

    def check_parameters(self, change):
        """Check if enough parameters have been provided to build the task.

        This methodd should fire the config_ready event each time it is called
        sending True if everything is allright, False otherwise.

        """
        err_str = '''This method should be implemented by subclasses of
        AbstractConfigTask. This method is called each time a trait is changed
        to check if enough parameters has been provided to build the task.'''
        raise NotImplementedError(cleandoc(err_str))

    def build_task(self):
        """This method use the user parameters to build the task object

         Returns
        -------
            task : BaseTask
                Task object built using the user parameters. Ready to be
                inserted in a task hierarchy.

        """
        err_str = '''This method should be implemented by subclasses of
        AbstractConfigTask. This method is called when the user validate its
        choices and that the task must be built.'''
        raise NotImplementedError(cleandoc(err_str))

    def _default_task_name(self):
        names = self.manager.auto_names
        if names:
            return random.choice(names)
        else:
            return ''


class PyConfigTask(AbstractConfigTask):
    """  Standard configurer for python tasks.

    This configurer is suitable for most python task whose initialisation
    simply requires a name.

    """

    # Docstring of the class to help pepole know what they are going to create.
    task_doc = Str()

    def __init__(self, **kwargs):
        super(PyConfigTask, self).__init__(**kwargs)
        self.task_doc = getdoc(self.task_class).replace('\n', ' ')

    def build_task(self):
        return self.task_class(task_name=self.task_name)

    @observe('task_name')
    def check_parameters(self, change):
        """ Observer notifying that the configurer is ready to build.

        """
        if self.task_name != '':
            self.config_ready = True
        else:
            self.config_ready = False


class IniConfigTask(AbstractConfigTask):
    """ Configurer for template task.

    This configurer use the data stored about a task hierarchy to rebuild it
    from scratch.

    """
    # Path to the file storing the hierarchy.
    template_path = Unicode()

    # Description of the template.
    template_doc = Str()

    def __init__(self, **kwargs):
        super(IniConfigTask, self).__init__(**kwargs)
        if self.template_path:
            _, doc = load_template(self.template_path)
            self.template_doc = doc

    @observe('task_name')
    def check_parameters(self, change):
        if self.task_name is not '':
            self.config_ready = True
        else:
            self.config_ready = False

    def build_task(self):
        """ Build the task stored in the selected template.

        """
        config, _ = load_template(self.template_path)
        built_task = build_task_from_config(config, self.manager)
        return built_task
