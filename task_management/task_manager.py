# -*- coding: utf-8 -*-
"""
"""
from traits.api import (HasTraits, List, Dict, Type, Str, File, Directory, Instance,
                        on_trait_change)
from traitsui.api import (View, VGroup, HGroup, UItem, ListStrEditor)

from tasks import AbstractTask, ComplexTask, known_py_tasks
from filters import task_filters, AbstractTaskFilter

import os
from inspect import getdoc
from configobj import ConfigObj

from watchdog.observers import Observer
from watchdog.observers.api import ObservedWatch
from watchdog.events import FileSystemEventHandler, FileCreatedEvent,\
                            FileDeletedEvent, FileMovedEvent

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

class TaskManager(HasTraits):
    """
    """

    py_tasks = List(Type(AbstractTask), known_py_tasks)

    template_folder = Directory('tasks/template')
    template_tasks = List(File)
    observer = Instance(Observer,())
    event_handler = Instance(FileListUpdater)
    watch = Instance(ObservedWatch)

    task_filters = Dict(Str,Type(AbstractTaskFilter))
    task_filters_name = List(Str)
    selected_task_filter_name = Str

    tasks = Dict(Str)
    tasks_name = List(Str)
    selected_task_name = Str
    selected_task_docstring = Str

    traits_view = View(
                    VGroup(
                        HGroup(
                            UItem('task_filters_name',
                                  editor = ListStrEditor(
                                      selected = 'selected_task_filter_name'),
                                  ),
                            UItem('tasks_name',editor = ListStrEditor(
                                      selected = 'selected_task_name'),
                                  ),
                            ),
                        HGroup(
                            UItem('selected_task_docstring',
                                  style = 'custom',
                                  width = 500,
                                  height = 50,
                                 ),
                            show_border = True,
                            label = 'Task description',
                            ),
                        ),
                    )

    def __init__(self, *args, **kwargs):
        super(TaskManager, self).__init__(*args, **kwargs)
        self.event_handler = FileListUpdater(self._update_list_file)
        self.watch = self.observer.schedule(self.event_handler,
                                            self.template_folder)
        self.observer.start()

        self.task_filters = task_filters
        self.task_filters_name = sorted(task_filters.keys())
        self.selected_task_filter_name = 'All'
        self._update_list_file()

    def get_task(self):
        """
        """
        # return a dictionnary containing at least the class and potentially the
        # template for a complex task
        selected_task = self.tasks[self.selected_task_name]
        if issubclass(selected_task, AbstractTask):
            return {'class' : selected_task}
        else:
            return {'class' : ComplexTask,
                    'preference' : selected_task}

    @on_trait_change('selected_task_filter_name')
    def _new_task_filter(self, new):
        """
        """
        task_filter_class = self.task_filters[new]
        task_filter = task_filter_class(py_tasks = self.py_tasks,
                                        template_tasks = self.template_tasks)
        self.tasks = task_filter.filter_tasks()
        self.tasks_name = sorted(self.tasks.keys())

    @on_trait_change('selected_task_name')
    def _new_task(self, new):
        """
        """
        task = self.tasks[new]
        if task in self.py_tasks:
            self.selected_task_docstring = getdoc(task)
        else:
            path = os.path.abspath(task)
            config = ConfigObj(path)
            if config.has_key('docstring'):
                self.selected_task_docstring = config['docstring']
            else:
                self.selected_task_docstring = ''

    def _update_list_file(self):
        """
        """
        # sorted files only
        path = self.template_folder
        tasks = sorted(f for f in os.listdir(path)
                           if (os.path.isfile(os.path.join(path, f))
                           and f.endswith('.ini')))
        self.template_tasks = tasks
        self._new_task_filter(self.selected_task_filter_name)

if __name__ == "__main__":
    __package__ = 'task_management.task_manager'
    TaskManager().configure_traits()