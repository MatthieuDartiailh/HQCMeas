# -*- coding: utf-8 -*-
"""
"""
from traits.api import (HasTraits, List, Dict, Type, Str, File, Directory,
                        Instance, Bool, on_trait_change)
from traitsui.api import (View, VGroup, HGroup, UItem, ListStrEditor,
                          EnumEditor)

import os
from inspect import getdoc, isclass
from configobj import ConfigObj

from watchdog.observers import Observer
from watchdog.observers.api import ObservedWatch
from watchdog.events import (FileSystemEventHandler, FileCreatedEvent,
                            FileDeletedEvent, FileMovedEvent)

from .tasks import AbstractTask, KNOWN_PY_TASKS
from ..task_management import tasks
from .filters import task_filters, AbstractTaskFilter

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

class TaskManager(HasTraits):
    """
    """

    py_tasks = List(Type(AbstractTask), KNOWN_PY_TASKS)

    template_folder = Directory(os.path.join(MODULE_PATH,'tasks/templates'))
    template_tasks = List(File)
    observer = Instance(Observer,())
    event_handler = Instance(FileListUpdater)
    watch = Instance(ObservedWatch)

    task_filters = Dict(Str, Type(AbstractTaskFilter), task_filters)
    task_filters_name = List(Str)
    selected_task_filter_name = Str('All')

    tasks = Dict(Str)
    tasks_name = List(Str)
    selected_task_name = Str
    selected_task_docstring = Str

    filter_visible = Bool(True)

    traits_view = View(
                    VGroup(
                        HGroup(
                            UItem('task_filters_name',
                                  editor = ListStrEditor(
                                      editable = False,
                                      selected = 'selected_task_filter_name'),
                                  ),
                            UItem('tasks_name',editor = ListStrEditor(
                                      selected = 'selected_task_name',
                                      editable = False),
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

    builder_view = View(
                    VGroup(
                        UItem('selected_task_filter_name',
                              editor = EnumEditor(name = 'task_filters_name'),
                              defined_when = 'filter_visible'),
                        UItem('tasks_name',editor = ListStrEditor(
                                             selected = 'selected_task_name',
                                             editable = False),
                             ),
                        show_border = True,
                        label = 'Task selection',
                        ),
                    )

    def __init__(self, *args, **kwargs):
        super(TaskManager, self).__init__(*args, **kwargs)
        self.task_filters_name = sorted(task_filters.keys())
        self.event_handler = FileListUpdater(self._update_list_file)
        self.watch = self.observer.schedule(self.event_handler,
                                            self.template_folder)
        self.observer.start()

        self._update_list_file()

    def get_task(self):
        """
        """
        # return a dictionnary containing at least the class and potentially the
        # template for a complex task
        selected_task = self.tasks[self.selected_task_name]
        if isclass(selected_task):
            return {'class' : selected_task}
        else:
            template_path = os.path.join(self.template_folder, selected_task)
            task_class_name = ConfigObj(template_path)['task_class']
            return {'class' : getattr(tasks, task_class_name),
                    'template_path' : template_path}

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
        self._new_task_filter(self.selected_task_filter_name)