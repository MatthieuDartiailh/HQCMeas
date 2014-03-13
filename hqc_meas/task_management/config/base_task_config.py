# -*- coding: utf-8 -*-
#==============================================================================
# module : base_task_config.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
""" Standard task configurers.

:Contains:
    AbstractConfigTask
    PyConfigTask
    IniConfigTask

"""

from atom.api import (Atom, Str, Bool, Unicode, Subclass, ForwardTyped,
                      observe)

from inspect import getdoc, cleandoc

from ...tasks.api import BaseTask, RootTask
from ..templates import load_template


# Circular import protection
def task_manager():
    from ..manager_plugin import TaskManagerPlugin
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
        _, doc = load_template(self.template_path)
        self.template_doc = doc

    @observe('task_name')
    def check_parameters(self, change):
        if self.task_name is not '':
            self.config_ready = True
        else:
            self.config_ready = False

    def build_task(self):
        """
        """
        config, _ = load_template(self.template_path)
        #Handle the case of an attempt to make a root task of a task which is
        #not a ComplexTask. built_task will be returned but task will be the
        #object used for the following manipulations.
        task_class = self._get_task(config['task_class'])
        if 'ComplexTask' not in [c.__name__ for c in type.mro(task_class)]:
            built_task = RootTask()
            task = task_class(task_name=config['task_name'])
            built_task.children.append(task)
        else:
            task = task_class(task_name=self.task_name)
            built_task = task

        parameters = self._prepare_parameters(config)
        task.update_members_from_preferences(**parameters)
        return built_task

    def build_task_from_config(self, config):
        """ Build a task hierarchy from a configobj.Section.

        Parameters:
        ----------
            config : configobj.Section
                Section holding the infos to build the task hierarchy.

        Returns
        -------
            task : instance(AbstractTask)
                Task object built using the user parameters.

        """
        built_task = RootTask(task_name='Root')
        parameters = self._prepare_parameters(config)
        built_task.update_members_from_preferences(**parameters)
        return built_task

    def _build_child(self, section):
        """ Build a child task of the hierarchy using its config.

        Parameters:
        ----------
            section : configobj.Section
                Scetion storing the necessary infos to build the child.

        Returns:
        -------
            task:
                Built child task.

        """
        task = self._get_task(section['task_class'])(task_name=
                                                     section['task_name'])
        parameters = self._prepare_parameters(section)
        task.update_members_from_preferences(**parameters)

        return task

    def _prepare_parameters(self, section):
        """ Assemble task parameters, ie attr and childs.

        Parameters:
            section : Section
                Section describing the parameters which must be sent to the
                task.

        Return:
            parameters : dict
                Dictionnary holding the parameters to be passed to a task.

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
                if key in parameters:
                    parameters[key].append(self._build_child(section[entry]))
                else:
                    parameters[key] = [self._build_child(section[entry])]

        return parameters

    def _get_task(self, name):
        """ Helper to retrieve a task class from the manager.

        """
        tasks = self.manager.tasks_request([name], use_class_names=True)
        return tasks.values()[0]
