# -*- coding: utf-8 -*-
"""
"""
from atom.api import (Atom, List, Dict, Str, Unicode,Property, observe,
                      Typed)

import os
from inspect import getdoc, isclass
from configobj import ConfigObj

from watchdog.observers import Observer
from watchdog.observers.api import ObservedWatch
from watchdog.events import (FileSystemEventHandler, FileCreatedEvent,
                            FileDeletedEvent, FileMovedEvent)

from .. import tasks
from ..tasks import BaseTask, KNOWN_PY_TASKS
from .filters import TASK_FILTERS, AbstractTaskFilter
from ..atom_util import Subclass

MODULE_PATH = os.path.dirname(__file__)

class FileListUpdater(FileSystemEventHandler):
    """
    """
    def __init__(self, handler):
        self.handler = handler

    def on_created(self, event):
        super(FileListUpdater, self).on_created(event)
        if isinstance(event, FileCreatedEvent):
            self.handler()

    def on_deleted(self, event):
        super(FileListUpdater, self).on_deleted(event)
        if isinstance(event, FileDeletedEvent):
            self.handler()

    def on_moved(self, event):
        super(FileListUpdater, self).on_deleted(event)
        if isinstance(event, FileMovedEvent):
            self.handler()

class TaskManager(Atom):
    """
    """

    py_tasks = List(Subclass(BaseTask), KNOWN_PY_TASKS)
    
    template_folder = Unicode(os.path.realpath(
                                    os.path.join(MODULE_PATH,
                                        '../tasks/templates')))
    template_tasks = List(Unicode())
    
    observer = Typed(Observer,())
    event_handler = Typed(FileListUpdater)
    watch = Typed(ObservedWatch)

    task_filters = Dict(Str(), Subclass(AbstractTaskFilter), TASK_FILTERS)
    selected_task_filter_name = Str('All')

    tasks = Dict(Str())
    selected_task_name = Str()
    selected_task_docstring = Str()
    task = Property()

    def __init__(self, *args, **kwargs):
        super(TaskManager, self).__init__(*args, **kwargs)
        self.event_handler = FileListUpdater(self._update_list_file)
        self.watch = self.observer.schedule(self.event_handler,
                                            self.template_folder)
        self.observer.start()

        self._update_list_file()

    @task.getter
    def _get_task(self):
        """
        """
        # return a dictionnary containing at least the class and potentially the
        # template for a complex task
        selected_task = self.tasks.get(self.selected_task_name, None)
        
        if selected_task is None:
            return None
        elif isclass(selected_task):
            return {'class' : selected_task}
        else:
            template_path = os.path.join(self.template_folder, selected_task)
            task_class_name = ConfigObj(template_path)['task_class']
            return {'class' : getattr(tasks, task_class_name),
                    'template_path' : template_path}

    @observe('selected_task_filter_name')
    def _new_task_filter(self, change):
        """
        """
        new = change['value']
        task_filter_class = self.task_filters[new]
        task_filter = task_filter_class(py_tasks = self.py_tasks,
                                        template_tasks = self.template_tasks)
        self.tasks = task_filter.filter_tasks()

    @observe('selected_task_name')
    def _new_task(self, change):
        """
        """
        new = change['value']
        if new:
            task = self.tasks[new]
            if task in self.py_tasks:
                doc = ''
                i = 0
                lines = getdoc(task).split('\n')
                while i < len(lines):
                    line = lines[i].strip()
                    if line:
                        doc += line + ' '
                    else:
                        break
                    i += 1
                self.selected_task_docstring = doc.strip()
            else:
                path = os.path.join(self.template_folder, task)
                doc_list = ConfigObj(path).initial_comment
                doc = ''
                for line in doc_list:
                    doc += line.replace('#','')
                self.selected_task_docstring = doc

    def _update_list_file(self):
        """
        """
        # sorted files only
        path = self.template_folder
        self.template_tasks = sorted(f for f in os.listdir(path)
                           if (os.path.isfile(os.path.join(path, f))
                           and f.endswith('.ini')))
        self._new_task_filter({'value' : self.selected_task_filter_name})