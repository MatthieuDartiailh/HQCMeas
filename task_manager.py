# -*- coding: utf-8 -*-


from traits.api import (HasTraits, List, Type, Str, Folder, Instance)

from tasks import AbstractTask, known_py_tasks


class TaskManager(HasTraits):
    """
    """

    py_tasks = List(Type(AbstractTask), known_py_tasks)
    template_folder = Folder
    template_tasks = List(Str)

    task_filters = List(Instance(BaseTaskFilter))