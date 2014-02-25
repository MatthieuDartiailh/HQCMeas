# -*- coding: utf-8 -*-
#==============================================================================
# module : instrument_manager.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
import os
import logging
from importlib import import_module
from atom.api import (Str, Dict, List, Unicode, Typed, Subclass, Tuple)

from watchdog.observers import Observer
from watchdog.events import (FileSystemEventHandler, FileCreatedEvent,
                             FileDeletedEvent, FileMovedEvent)
from inspect import cleandoc

from ..enaml_util.pref_plugin import HasPrefPlugin
from ..tasks.base_tasks import BaseTask
from .filters import AbstractTaskFilter, TASK_FILTERS
from .config import SPECIAL_CONFIG, CONFIG_MAP_VIEW, IniConfigTask


MODULE_PATH = os.path.dirname(__file__)


# XXXX Filters and Config being less prone to frequent udpates, no dynamic
# introspection is performed and the old system using variables defined in
# __init__ is kept. However as this might change in the future all the logic
# will be centralized in the manager just like for tasks, and all the variables
# will be defined to ease a future transition (save exceptions) only the
# refresh_methods will be dummies.
class TaskManagerPlugin(HasPrefPlugin):
    """
    """

    # Folders containings templates which should be loaded.
    templates_folders = List(Unicode(),
                             [os.path.realpath(
                                 os.path.join(MODULE_PATH,
                                              '../tasks/templates'))]
                             ).tag(pref=True)

    # Drivers loading exception
    tasks_loading = List(Unicode()).tag(pref=True)

    # List of all the known tasks
    tasks = List()

    # List of the filters
    filters = List(Str(), TASK_FILTERS.keys())

    def start(self):
        """ Start the plugin life-cycle.

        This method is called by the framework at the appropriate time.
        It should never be called by user code.

        """
        super(TaskManagerPlugin, self).start()
        self._refresh_template_tasks()
        self._refresh_tasks()
        self._refresh_filters()
        self._bind_observers()

    def stop(self):
        """ Stop the plugin life-cycle.

        This method is called by the framework at the appropriate time.
        It should never be called by user code.

        """
        super(TaskManagerPlugin, self).stop()
        self._unbind_observers()
        self._tasks.clear()
        self._template_tasks.clear()
        self._filters.clear()

    def tasks_request(self, tasks):
        """ Give access to task classes.

        NB : This function won't work with template

        Parameters
        ----------
        tasks : list(str)
            The names of the requested tasks

        Returns
        -------
        tasks : dict
            The required tasks class as a dict {name: class}
        """
        return {key: val for key, val in self._py_tasks.iteritems()
                if key in tasks}

    def filter_tasks(self, filter_name):
        """ Filter the known using the specified filter.

        Parameters
        ----------
        filter_name : str
            Name of the filter to use

        Returns
        -------
        tasks : list(str)
            Tasks selected by the filter

        """
        # TODO implement
        pass

    def config_request(self, task_name):
        """ Access the proper config for a task

        Parameters
        ----------
        task_name : str
            Name of the task for which a config is required

        Returns
        -------
        config : tuple
            Tuple containing the config object requested, and its visualisation

        """
        # TODO implement
        pass

    #--- Private API ----------------------------------------------------------
    # Tasks implemented in Python
    _py_tasks = Dict(Str(), Subclass(BaseTask))

    # Template tasks (store full path to .ini)
    _template_tasks = Dict(Str(), Unicode())

    # Task filters
    _filters = Dict(Str(), Subclass(AbstractTaskFilter), TASK_FILTERS)

    # Task config dict for python tasks
    _configs = Dict(Subclass(BaseTask), Tuple())

    # Watchdog observer
    _observer = Typed(Observer, ())

    def _refresh_template_tasks(self):
        """ Refresh the known profiles

        """
        templates = {}
        for path in self.profiles_folders:
            filenames = sorted(f for f in os.listdir(path)
                               if (os.path.isfile(os.path.join(path, f))
                                   and f.endswith('.ini')))

            for filename in filenames:
                template_name = self._normalise_name(filename)
                template_path = os.path.join(path, filename)
                # Beware redundant names are overwrited
                templates[template_name] = template_path

        self._template_tasks = templates
        self.tasks = list(self._py_tasks.keys) + list(templates.keys())

    def _refresh_tasks(self):
        """ Refresh the known tasks.

        """
        path = os.path.join(MODULE_PATH, '../tasks')
        modules = sorted(m[:-3] for m in os.listdir(path)
                         if (os.path.isfile(os.path.join(path, m))
                             and m.endswith('.py')))
        modules.remove('__init__')
        for mod in modules[:]:
            if mod in self.tasks_loading:
                modules.remove(mod)

        tasks = {}
        tasks_packages = []
        failed = {}
        self._explore_modules(modules, tasks, tasks_packages, failed)

        # Remove packages which should not be explored
        for pack in tasks_packages[:]:
            if pack in self.tasks_loading:
                tasks_packages.remove(pack)

        # Explore packages
        while tasks_packages:
            pack = tasks_packages.pop(0)
            pack_path = os.path.join(path, os.path.join(pack.split('.')))
            if not os.path.isdir(pack_path):
                log = logging.getLogger(__name__)
                mess = '{} is not a valid directory.({})'.format(pack,
                                                                 pack_path)
                log.error(mess)
                failed[pack] = mess
                continue

            modules = sorted(pack + '.' + m[:-3] for m in os.listdir(pack_path)
                             if (os.path.isfile(os.path.join(path, m))
                                 and m.endswith('.py')))
            try:
                modules.removes(pack + '.__init__')
            except ValueError:
                log = logging.getLogger(__name__)
                mess = cleandoc('''{} is not a valid Python package (miss
                    __init__.py).'''.format(pack))
                log.error(mess)
                failed[pack] = mess
                continue

            # Remove modules which should not be imported
            for mod in modules[:]:
                if mod in self.tasks_loading:
                    modules.remove(mod)

            self._explore_modules(modules, tasks, tasks_packages,
                                  failed, prefix=pack)

            # Remove packages which should not be explored
            for pack in tasks_packages[:]:
                if pack in self.drivers_loading:
                    tasks_packages.remove(pack)

        self._py_tasks = tasks
        self.tasks = list(tasks.keys) + list(self._template_tasks.keys())

        # TODO do something with failed

    def _refresh_filters(self):
        """ Place holder for a future filter discovery function

        """
        self._filters = TASK_FILTERS

    def _refresh_config(self):
        """ Place holder for a future config discovery function

        """
        mapping = {}
        for key, val in SPECIAL_CONFIG:
            mapping[key] = (val, CONFIG_MAP_VIEW[val])

        self._configs = mapping

    def _explore_modules(self, modules, tasks, packages, failed,
                         prefix=None):
        """ Explore a list of modules.

        Parameters
        ----------
        modules : list
            The list of modules to explore

        tasks : dict
            A dict in which discovered tasks will be stored.

        packages : list
            A list in which discovered packages will be stored.


        failed : list
            A list in which failed imports will be stored.
        """
        for mod in modules:
            try:
                m = import_module('..tasks.' + mod)
            except Exception as e:
                log = logging.getLogger(__name__)
                mess = 'Failed to import {} : {}'.format(mod, e.message)
                log.error(mess)
                failed[mod] = mess
                continue

            if hasattr(m, 'KNOWN_PY_TASKS'):
                tasks.update({self._normalize_name(task.__name__): task
                              for task in m.KNOWN_PY_TASKS})

            if hasattr(m, 'TASK_PACKAGES'):
                if prefix is not None:
                    packs = [prefix + '.' + pack for pack in m.TASK_PACKAGES]
                else:
                    packs = m.TASK_PACKAGES
                packages.extend(packs)

    def _bind_observers(self):
        """ Setup the observers for the plugin.

        """
        for folder in self.profiles_folders:
            handler = _FileListUpdater(self._refresh_template_tasks)
            self._observer.schedule(handler, folder, recursive=True)

    def _unbind_observers(self):
        """ Remove the observers for the plugin.

        """
        self._observer.unchedule_all()

    @staticmethod
    def _normalise_name(name):
        """Normalize the name of the profiles by replacing '_' by spaces,
        removing the extension, and adding spaces between 'aA' sequences.
        """
        if name.endswith('.ini') or name.endswith('Task'):
            name = name[:-4] + '\0'
        aux = ''
        for i, char in enumerate(name):
            if char == '_':
                aux += ' '
                continue

            if char != '\0':
                if char.isupper() and i != 0:
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


class _FileListUpdater(FileSystemEventHandler):
    """Simple watchdog handler used for auto-updating the profiles list

    """
    def __init__(self, handler):
        self.handler = handler

    def on_created(self, event):
        super(_FileListUpdater, self).on_created(event)
        if isinstance(event, FileCreatedEvent):
            self.handler()

    def on_deleted(self, event):
        super(_FileListUpdater, self).on_deleted(event)
        if isinstance(event, FileDeletedEvent):
            self.handler()

    def on_moved(self, event):
        super(_FileListUpdater, self).on_deleted(event)
        if isinstance(event, FileMovedEvent):
            self.handler()
