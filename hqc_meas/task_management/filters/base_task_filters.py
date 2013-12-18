# -*- coding: utf-8 -*-
"""
"""

from atom.api import (Atom, List, Unicode)
# BaseLoopTask, , InstrumentTask
from ...tasks import (BaseTask,ComplexTask)
from ...atom_util import Subclass

class AbstractTaskFilter(Atom):
    """
    """

    py_tasks = List(Subclass(BaseTask))
    template_tasks = List(Unicode())

    def filter_tasks(self):
        """
        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractTaskFilter. This method is called when the program requires\
        the task filter to filter the list of available tasks'
        raise NotImplementedError(err_str)

    @staticmethod
    def normalise_name(name):
        """
        """
        if name.endswith('.ini') or name.endswith('Task'):
            name = name[:-4] + '\0'
        aux = ''
        for i, char in enumerate(name):
            if char == '_':
                aux += ' '
                continue

            if char != '\0':
                if char.isupper() and i!=0 :
                    if name[i-1].islower():
                        if name[i+1].islower():
                            aux += ' ' + char.lower()
                        else:
                            aux += ' ' + char
                    else:
                        if name[i+1].islower():
                            aux += ' ' + char.lower()
                        else:
                            aux += char
                else:
                    if i == 0:
                        aux += char.upper()
                    else:
                        aux += char
        return aux

class AllTaskFilter(AbstractTaskFilter):
    """
    """

    def filter_tasks(self):
        """
        """
        tasks = {}
        for py_task in self.py_tasks:
            task_name = self.normalise_name(py_task.__name__)
            tasks[task_name] = py_task

        for template_task in self.template_tasks:
            task_name = self.normalise_name(template_task)
            tasks[task_name] = template_task

        return tasks

class PyTaskFilter(AbstractTaskFilter):
    """
    """

    def filter_tasks(self):
        """
        """
        tasks = {}
        for py_task in self.py_tasks:
            task_name = self.normalise_name(py_task.__name__)
            tasks[task_name] = py_task

        return tasks

class TemplateTaskFilter(AbstractTaskFilter):
    """
    """

    def filter_tasks(self):
        """
        """
        tasks = {}
        for template_task in self.template_tasks:
            task_name = self.normalise_name(template_task)
            tasks[task_name] = template_task

        return tasks

class SimpleTaskFilter(AbstractTaskFilter):
    """
    """

    def filter_tasks(self):
        """
        """
        tasks = {}
        for py_task in self.py_tasks:
            if not issubclass(py_task, ComplexTask):
                task_name = self.normalise_name(py_task.__name__)
                tasks[task_name] = py_task

        return tasks

class LoopTaskFilter(AbstractTaskFilter):
    """
    """
    def filter_tasks(self):
        """
        """
        tasks = {}
        for py_task in self.py_tasks:
            if issubclass(py_task, BaseLoopTask) :
                task_name = self.normalise_name(py_task.__name__)
                tasks[task_name] = py_task

        return tasks


class LoopableTaskFilter(AbstractTaskFilter):
    """
    """

    def filter_tasks(self):
        """
        """
        tasks = {}
        for py_task in self.py_tasks:
            if hasattr(py_task, 'loopable') and py_task.loopable:
                task_name = self.normalise_name(py_task.__name__)
                tasks[task_name] = py_task

        return tasks

class InstrumentTaskFilter(AbstractTaskFilter):
    """
    """

    def filter_tasks(self):
        """
        """
        tasks = {}
        for py_task in self.py_tasks:
            if issubclass(py_task, InstrumentTask):
                task_name = self.normalise_name(py_task.__name__)
                tasks[task_name] = py_task

        return tasks