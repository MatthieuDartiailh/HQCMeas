# -*- coding: utf-8 -*-
"""
"""

from traits.api import (HasTraits, List, Type, File)
import re

from ..tasks import AbstractTask, LoopTask, ComplexTask

class AbstractTaskFilter(HasTraits):
    """
    """

    py_tasks = List(Type(AbstractTask))
    template_tasks = List(File)

    def filter_tasks(self):
        """
        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractTaskFilter. This method is called when the program requires\
        the task filter to filter the list of available tasks'
        raise NotImplementedError(err_str)

    def normalise_name(self, name):
        """
        """
        name = re.sub('(?<!^)(?=[A-Z])', ' ', name)
        name = re.sub('_', ' ', name)
        name = re.sub('.ini', '', name)
        return name.capitalize()

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
            if py_task is not ComplexTask and py_task is not LoopTask:
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
            if hasattr(py_task, 'loopable'):
                if py_task.loopable:
                    task_name = self.normalise_name(py_task.__name__)
                    tasks[task_name] = py_task

        return tasks