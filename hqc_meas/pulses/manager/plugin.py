# -*- coding: utf-8 -*-
# =============================================================================
# module : pulses/manager/plugin.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
import os
import logging
import enaml
from importlib import import_module
from atom.api import (Str, Dict, List, Unicode, Typed, Tuple)

from watchdog.observers import Observer
from watchdog.events import (FileSystemEventHandler, FileCreatedEvent,
                             FileDeletedEvent, FileMovedEvent)
from inspect import cleandoc

from hqc_meas.utils.has_pref_plugin import HasPrefPlugin
from .templates_io import load_template
from ..pulse import Pulse
from ..base_sequences import Sequence, RootSequence
with enaml.imports():
    from ..pulse_view import PulseView
    from ..sequences_views import (SequenceView, RootSequenceView)


PACKAGE_PATH = os.path.join(os.path.dirname(__file__), '..')

MODULE_ANCHOR = 'hqc_meas.pulses'


class PulsesManagerPlugin(HasPrefPlugin):
    """
    """
    #: Folders containings templates which should be loaded.
    templates_folders = List(Unicode(),
                             [os.path.realpath(
                                 os.path.join(PACKAGE_PATH,
                                              'templates'))]
                             ).tag(pref=True)

    #: Sequences loading exception.
    sequences_loading = List(Unicode()).tag(pref=True)

    #: Contexts loading exception.
    contexts_loading = List(Unicode()).tag(pref=True)

    #: Shapes loading exceptions.
    shapes_loading = List(Unicode()).tag(pref=True)

    #: List of all the known sequences.
    sequences = List(Str())

    #: List of all the known contexts
    contexts = List(Str())

    #: List of all known shape.
    shapes = List(Str())

    def start(self):
        """ Start the plugin life-cycle.

        This method is called by the framework at the appropriate time.
        It should never be called by user code.

        """
        super(PulsesManagerPlugin, self).start()
        path = os.path.realpath(os.path.join(PACKAGE_PATH,
                                             'templates'))
        if not os.path.isdir(path):
            os.mkdir(path)
        self._refresh_template_sequences()
        self._refresh_sequences()
        self._refresh_contexts()
        self._refresh_shapes()
        self._bind_observers()

    def stop(self):
        """ Stop the plugin life-cycle.

        This method is called by the framework at the appropriate time.
        It should never be called by user code.

        """
        super(PulsesManagerPlugin, self).stop()
        self._unbind_observers()
        self._sequences.clear()
        self._template_sequences.clear()
        self._contexts.clear()
        self._shapes.clear()

    def sequences_request(self, sequences, use_class_names=False,
                          views=True):
        """ Give access to sequence infos.

        Parameters
        ----------
        sequences : list(str)
            The names of the requested sequences.
        use_class_names : bool, optional
            Should the search be performed using class names rather than
            sequence names.
        views : bool
            When false views are not returned alongside the class.

        Returns
        -------
        sequences : dict
            The required sequences infos as a dict. For Python tasks the entry
            will contain the class and the view ({name: (class, view)}).
            If use_class_names is True the class name will be used.
            For templates the entry will contain the path, the data as a
            ConfigObj object and the doc ({name : (path, data, doc)})

        """
        answer = {}

        if not use_class_names:
            missing_py = set([name for name in sequences
                              if name not in self._sequences.keys()])
            missing_temp = set([name for name in sequences
                                if name not in self._template_sequences.keys()]
                               )
            missing = list(set.intersection(missing_py, missing_temp))

            answer.update({key: val for key, val in self._sequences.iteritems()
                           if key in sequences})

            answer.update({key: tuple([val] + list(load_template(val)))
                           for key, val in self._template_sequences.iteritems()
                           if key in sequences})
        else:
            class_names = {val[0].__name__: val
                           for val in self._sequences.values()}

            missing = [name for name in sequences
                       if name not in class_names]

            answer.update({key: val for key, val in class_names.iteritems()
                           if key in sequences})

        if not views:
            answer = {k: v[0] for k, v in answer.iteritems()}

        return answer, missing

    def contexts_request(self, contexts, use_class_names=False,
                         views=True):
        """ Give access to context infos.

        Parameters
        ----------
        contexts : list(str)
            The names of the requested contexts.
        use_class_names : bool, optional
            Should the search be performed using class names rather than
            context names.
        views : bool
            When false views are not returned alongside the class.

        Returns
        -------
        contexts : dict
            The required contexts infos as a dict {name: (class, view)}.
            If use_class_names is True the class name will be used.

        """
        answer = {}

        if not use_class_names:
            missing = [name for name in contexts
                       if name not in self._contexts.keys()]

            answer.update({key: val for key, val in self._contexts.iteritems()
                           if key in contexts})

        else:
            class_names = {val[0].__name__: val
                           for val in self._contexts.values()}

            missing = [name for name in contexts
                       if name not in class_names]

            answer.update({key: val for key, val in class_names.iteritems()
                           if key in contexts})

        if not views:
            answer = {k: v[0] for k, v in answer.iteritems()}

        return answer, missing

    def shapes_request(self, shapes, use_class_names=False, views=True):
        """ Give access to shape infos.

        Parameters
        ----------
        shapes : list(str)
            The names of the requested shapes.
        use_class_names : bool, optional
            Should the search be performed using class names rather than
            context names.
        views : bool
            When flase views are not returned alongside the class.

        Returns
        -------
        shapes : dict
            The required shapes infos as a dict {name: (class, view)}.
            If use_class_names is True the class name will be used.

        """
        answer = {}

        if not use_class_names:
            missing = [name for name in shapes
                       if name not in self._shapes.keys()]

            answer.update({key: val for key, val in self._shapes.iteritems()
                           if key in shapes})

        else:
            class_names = {val[0].__name__: val
                           for val in self._shapes.values()}

            missing = [name for name in shapes
                       if name not in class_names]

            answer.update({key: val for key, val in class_names.iteritems()
                           if key in shapes})

        if not views:
            answer = {k: v[0] for k, v in answer.iteritems()}

        return answer, missing

    def report(self):
        """ Give access to the failures which happened at startup.

        """
        return self._failed

    # --- Private API ---------------------------------------------------------
    # Sequences implemented in Python
    _sequences = Dict(Str(), Tuple())

    # Template tasks (store full path to .ini)
    _template_sequences = Dict(Str(), Unicode())

    # Task filters
    _contexts = Dict(Str(), Tuple())

    # Task config dict for python tasks (task_class: (config, view))
    _shapes = Dict(Str(), Tuple())

    # Dict holding the list of failures which happened during loading
    _failed = Dict()

    # Watchdog observer
    _observer = Typed(Observer, ())

    def _refresh_template_sequences(self):
        """ Refresh the known template sequences.

        """
        templates = {}
        for path in self.templates_folders:
            if os.path.isdir(path):
                filenames = sorted(f for f in os.listdir(path)
                                   if (os.path.isfile(os.path.join(path, f))
                                       and f.endswith('.ini')))

                for filename in filenames:
                    template_name = self._normalise_name(filename)
                    template_path = os.path.join(path, filename)
                    # Beware redundant names are overwrited
                    templates[template_name] = template_path
            else:
                logger = logging.getLogger(__name__)
                logger.warn('{} is not a valid directory'.format(path))

        self._template_sequences = templates
        self.sequences = list(self._sequences.keys()) + list(templates.keys())

    def _refresh_sequences(self):
        """ Refresh the known sequences.

        """
        path = os.path.join(PACKAGE_PATH, 'sequences')
        failed = {}

        modules, v_modules = self._explore_package('sequences', path, failed,
                                                   self.sequences_loading)

        sequences = {}
        views = {}
        self._explore_modules(modules, sequences, 'SEQUENCES', failed)
        self._explore_views(v_modules, views, 'SEQUENCES_VIEWS', failed)

        valid_sequences = {k: (v, views[v.__name__])
                           for k, v in sequences.iteritems()
                           if v.__name__ in views}
        valid_sequences['Sequence'] = (Sequence, SequenceView)
        valid_sequences['RootSequence'] = (RootSequence, RootSequenceView)
        valid_sequences['Pulse'] = (Pulse, PulseView)

        self._sequences = valid_sequences
        self.sequences = list(valid_sequences.keys()) +\
            list(self._template_sequences.keys())

        self._failed = failed

    def _refresh_contexts(self):
        """ Refresh the known contexts.

        """
        path = os.path.join(PACKAGE_PATH, 'contexts')
        failed = {}

        modules, v_modules = self._explore_package('contexts', path, failed,
                                                   self.contexts_loading)

        contexts = {}
        views = {}
        self._explore_modules(modules, contexts, 'CONTEXTS', failed)
        self._explore_views(v_modules, views, 'CONTEXTS_VIEWS', failed)

        valid_contexts = {k: (v, views[v.__name__])
                          for k, v in contexts.iteritems()
                          if v.__name__ in views}

        self._contexts = valid_contexts
        self.contexts = list(valid_contexts.keys())

        self._failed = failed

    def _refresh_shapes(self):
        """ Refresh the known shapes.

        """
        path = os.path.join(PACKAGE_PATH, 'shapes')
        failed = {}

        modules, v_modules = self._explore_package('shapes', path, failed,
                                                   self.shapes_loading)

        shapes = {}
        views = {}
        self._explore_modules(modules, shapes, 'SHAPES', failed)
        self._explore_views(v_modules, views, 'SHAPES_VIEWS', failed)

        valid_shapes = {k: (v, views[v.__name__])
                        for k, v in shapes.iteritems()
                        if v.__name__ in views}

        self._shapes = valid_shapes
        self.shapes = list(valid_shapes.keys())

        self._failed = failed

    def _explore_package(self, pack, pack_path, failed, exceptions):
        """ Explore a package.

        Parameters
        ----------
        pack : str
            The package name relative to the packages pulses.
            (ex : sequences)

        pack_path : unicode
            Path of the package to explore

        failed : dict
            A dict in which failed imports will be stored.

        exceptions: list
            Names of the modules which should not be loaded.

        Returns
        -------
        modules : list
            List of string indicating modules which can be imported

        v_modules : list
            List of string indicating enaml modules which can be imported

        """
        if not os.path.isdir(pack_path):
            log = logging.getLogger(__name__)
            mess = '{} is not a valid directory.({})'.format(pack,
                                                             pack_path)
            log.error(mess)
            failed[pack] = mess
            return [], []

        modules = sorted(pack + '.' + m[:-3] for m in os.listdir(pack_path)
                         if (os.path.isfile(os.path.join(pack_path, m))
                             and m.endswith('.py')))

        try:
            modules.remove(pack + '.__init__')
        except ValueError:
            log = logging.getLogger(__name__)
            mess = cleandoc('''{} is not a valid Python package (miss
                __init__.py).'''.format(pack))
            log.error(mess)
            failed[pack] = mess
            return [], []

        # Remove modules which should not be imported
        for mod in modules[:]:
            if mod in exceptions:
                modules.remove(mod)

        # Look for enaml definitions
        v_path = os.path.join(pack_path, 'views')
        if not os.path.isdir(v_path):
            log = logging.getLogger(__name__)
            mess = '{}.views is not a valid directory.({})'.format(pack,
                                                                   v_path)
            log.error(mess)
            failed[pack] = mess
            return [], []

        v_modules = sorted(pack + '.views.' + m[:-6]
                           for m in os.listdir(v_path)
                           if (os.path.isfile(os.path.join(v_path, m))
                               and m.endswith('.enaml')))

        if not os.path.isfile(os.path.join(pack_path, '__init__.py')):
            log = logging.getLogger(__name__)
            mess = cleandoc('''{} is not a valid Python package (miss
                __init__.py).'''.format(pack + '.views'))
            log.error(mess)
            failed[pack] = mess
            return [], []

        for mod in v_modules[:]:
            if mod in exceptions:
                v_modules.remove(mod)

        return modules, v_modules

    def _explore_modules(self, modules, founds, mod_var, failed):
        """ Explore a list of modules, looking for tasks.

        Parameters
        ----------
        modules : list
            The list of modules to explore

        found : dict
            A dict in which discovered objects will be stored.

        mod_var : str
            Name of the module variable to look for.

        failed : list
            A dict in which failed imports will be stored.

        """
        for mod in modules:
            try:
                m = import_module('.' + mod, MODULE_ANCHOR)
            except Exception as e:
                log = logging.getLogger(__name__)
                mess = 'Failed to import {} : {}'.format(mod, e)
                log.error(mess)
                failed[mod] = mess
                continue

            if hasattr(m, mod_var):
                var = getattr(m, mod_var)
                if isinstance(var, list):
                    founds.update({self._normalise_name(found.__name__): found
                                  for found in var})
                else:
                    founds.update(var)

    def _explore_views(self, modules, views, mod_var, failed):
        """ Explore a list of modules, looking for views.

        Parameters
        ----------
        modules : list
            The list of modules to explore

        views : dict
            A dict in which discovered views will be stored.

        mod_var : str
            Name of the module variable to look for.

        failed : list
            A list in which failed imports will be stored.

        """
        for mod in modules:
            try:
                with enaml.imports():
                    m = import_module('.' + mod, MODULE_ANCHOR)
            except Exception as e:
                log = logging.getLogger(__name__)
                mess = 'Failed to import {} : {}'.format(mod, e)
                log.error(mess)
                failed[mod] = mess
                continue

            if hasattr(m, mod_var):
                views.update(getattr(m, mod_var))

    def _bind_observers(self):
        """ Setup the observers for the plugin.

        """

        for folder in self.templates_folders:
            handler = _FileListUpdater(self._refresh_template_sequences)
            self._observer.schedule(handler, folder, recursive=True)

        self._observer.start()
        self.observe('sequences_loading', self._update_sequences)
        self.observe('templates_folders', self._update_templates)
        self.observe('contexts_loading', self._update_contexts)
        self.observe('shapes_loading', self._update_shapes)

    def _unbind_observers(self):
        """ Remove the observers for the plugin.

        """
        self.unobserve('sequences_loading', self._update_sequences)
        self.unobserve('contexts_loading', self._update_contexts)
        self.unobserve('shapes_loading', self._update_shapes)
        self.unobserve('templates_folders', self._update_templates)
        self._observer.unschedule_all()
        self._observer.stop()
        self._observer.join()

    def _update_sequences(self, change):
        """ Observer ensuring that loading preferences are taken into account.

        """
        self._refresh_sequences()

    def _update_contexts(self, change):
        """ Observer ensuring that loading preferences are taken into account.

        """
        self._refresh_contexts()

    def _update_shapes(self, change):
        """ Observer ensuring that loading preferences are taken into account.

        """
        self._refresh_shapes()

    def _update_templates(self, change):
        """ Observer ensuring that we observe the right template folders.

        """
        self._observer.unschedule_all()

        for folder in self.templates_folders:
            handler = _FileListUpdater(self._refresh_template_tasks)
            self._observer.schedule(handler, folder, recursive=True)

    @staticmethod
    def _normalise_name(name):
        """Normalize names by replacing '_' by spaces, removing the extension,
        and adding spaces between 'aA' sequences.
        """
        if name.endswith('.ini'):
            name = name[:-4] + '\0'
        elif name.endswith('Shape'):
            name = name[:-5] + '\0'
        else:
            name += '\0'
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
