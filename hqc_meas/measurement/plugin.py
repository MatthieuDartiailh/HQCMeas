# -*- coding: utf-8 -*-
#==============================================================================
# module : measure_plugin.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
import logging
from inspect import cleandoc
from atom.api import Typed, Unicode, Dict, ContainerList, List, Instance, Tuple
from time import sleep
from importlib import import_module

from hqc_meas.utils.has_pref_plugin import HasPrefPlugin
from .engines.base_engine import BaseEngine, Engine
from .monitors.base_monitor import Monitor
from .headers.base_header import Header
from .checks.base_checks import Check
from .measure import Measure


INVALID_MEASURE_STATUS = ['EDITING', 'SKIPPED', 'FAILED', 'COMPLETED',
                          'INTERRUPTED']

ENGINES_POINT = u'hqc_meas.measure.engines'

MONITORS_POINT = u'hqc_meas.measure.monitors'

HEADERS_POINT = u'hqc_meas.measure.headers'

CHECKS_POINT = u'hqc_meas.measure.checks'


# TODO handle extensions points
class MeasurePlugin(HasPrefPlugin):
    """
    """
    #--- Public API -----------------------------------------------------------
    # Have to be here otherwise lose tons of infos when closing workspace

    # List of (module_path, manifest_name) which should be regitered on
    # startup.
    manifests = List(Tuple()).tag(pref=True)

    # Currently edited measure.
    edited_measure = Typed(Measure)

    # Currently enqueued measures.
    enqueued_measures = ContainerList(Typed(Measure))

    # Currently run measure or last measure run.
    running_measure = Typed(Measure)

    # Dict holding the contributed Engine declarations.
    engines = Dict(Unicode(), Engine())

    # Currently selected engine represented by its manifest id.
    # TODO in refresh should check this engine exists, otherwise warn and put
    # it to ''
    selected_engine = Unicode().tag(pref=True)

    # Instance of the currently used engine.
    engine_instance = Instance(BaseEngine)

    # Dict holding the contributed Monitor declarations.
    monitors = Dict(Unicode(), Monitor())

    # Default monitors to use for new measures.
    default_monitors = List(Unicode()).tag(pref=True)

    # Dict holding the contributed Header declarations.
    headers = Dict(Unicode(), Header())

    # Default headers to use for new measures.
    default_headers = List(Unicode()).tag(pref=True)

    # Dict holding the contributed Check declarations.
    checks = Dict(Unicode(), Check())

    # Default checks to use for new measures.
    default_checks = List(Unicode()).tag(pref=True)

    # Internal flags.
    flags = Dict()

    def start(self):
        """
        """
        super(MeasurePlugin, self).start()

        # Register contributed plugin.
        for path, manifest_name in self.manifests:
            try:
                module = import_module(path)
                manifest = getattr(module, manifest_name)
                plugin = manifest()
                self.workbench.register(plugin)
                self._manifest_ids.append(plugin.id)

            except Exception:
                logger = logging.getLogger(__name__)
                logger.error('Failed to register manifest: {}'.format(path))

        # Refresh contribution and start observers.
        self._refresh_engines()
        self._refresh_monitors()
        self._refresh_headers()
        self._refresh_checks()
        self._bind_observers()

    def stop(self):
        """
        """
        # Unbind the observers.
        self._unbind_observers()

        # Unregister the plugin registered at start-up.
        for manifest_id in self._manifest_ids:
            self.workbench.unregister(manifest_id)

        # Clear ressources.
        self._engines.clear()
        self._monitors.clear()
        self._headers.clear()
        self._checks.clear()

    def start_measure(self, measure):
        """ Start a new measure.

        """
        logger = logging.getLogger(__name__)

        # Discard old monitors if there is any remaining.
        for monitor in self.running_measure.monitors:
            monitor.shutdown()

        self.running_measure = measure

        # Requesting profiles.
        profiles = measure.store('profiles')
        core = self.workbench.get_plugin('enaml.workbench.core')

        com = u'hqc_meas.instr_manager.profiles_request'
        res, profiles = core.invoke_command(com, {'profiles': list(profiles)},
                                            self._plugin)
        if not res:
            mes = cleandoc('''The profiles requested for the measurement {} are
                           not available, the measurement cannot be performed
                           '''.format(measure.name))
            logger.info(mes)

            # Simulate a message coming from the engine.
            done = {'value': ('SKIPPED', 'Failed to get requested profiles')}
            self._listen_to_engine(done)

        measure.root_task.run_time.update({'profiles': profiles})

        # Collect headers.
        measure.collect_headers(self.workbench)

        # Start the engine if it has not already been done.
        if not self.engine_instance:
            maker = self.engines[self.selected_engine]
            self.engine_instance = maker(self.workbench)

            # Connect signal handler to engine.
            self.engine_instance.observe('done', self._listen_to_engine)

        engine = self.engine_instance

        # Call engine prepare to run method.
        entries = measure.collect_entries_to_observe()
        engine.prepare_to_run(measure.root_task, entries)

        measure.status = 'RUNNING'
        measure.infos = 'The measure is running'

        # Connect new monitors, and start them.
        for monitor in measure.monitors:
            engine.observe('news', monitor.process_news)
            monitor.start()

        # Ask the engine to start the measure.
        engine.run()

    def stop_measure(self):
        """ Stop the currently active measure.

        """
        self.engine_instance.stop()

    def stop_processing(self):
        """ Stop processing the enqueued measure.

        """
        self.flags['stop_processing'] = True
        self.engine_instance.exit()

    def force_stop_measure(self):
        """ Force the engine to stop performing the current measure.

        """
        self.engine_instance.force_stop()

    def force_stop_processing(self):
        """ Force the engine to exit and stop processing measures.

        """
        self.flags['stop_processing'] = True
        self.engine_instance.force_exit()

    def find_next_measure(self):
        """ Find the next runnable measure in the queue.

        Returns
        -------
        measure : Measure
            First valid measurement in the queue or None if there is no
            available measure.

        """
        enqueued_measures = self._plugin.enqueued_measures
        i = 0
        measure = None
        # Look for a measure not being currently edited. (Can happen if the
        # user is editing the second measure when the first measure ends).
        while i < len(enqueued_measures):
            measure = enqueued_measures[i]
            if measure.status in INVALID_MEASURE_STATUS:
                i += 1
                measure = None
            else:
                break

        return measure

    #--- Private API ----------------------------------------------------------

    # Manifests ids of the plugin registered at start up.
    _manifest_ids = List(Unicode())

    def _listen_to_engine(self, change):
        """ Observer for the engine notifications.

        """
        status, infos = change['value']
        self.running_measure.status = status
        self.running_measure.infos = infos

        # Disconnect monitors.
        self.engine_instance.unobserve('news')

        # If we are supposed to stop, stop.
        if 'stop_processing' in self.flags:
            self.stop_processing()
            while not self.engine_instance.active:
                sleep(0.5)

        # Otherwise find the next measure, if there is none stop the engine.
        else:
            meas = self.find_next_measure()
            if meas is not None:
                self.start_measure(meas)
            else:
                self.stop_processing()
                while not self.engine_instance.active:
                    sleep(0.5)

    def _register_manifest(self, path, manifest_name):
        """
        """
        pass

    def _refresh_engines(self):
        """ Refresh the list of known engines.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(ENGINES_POINT)
        extensions = point.extensions
        if not extensions:
            self.engines.clear()
            return

        new_engines = {}
        old_engines = self.engines
        for extension in extensions:
            plugin_id = extension.plugin_id
            if plugin_id in old_engines:
                engine = old_engines[plugin_id]
            else:
                engine = self._load_engine(extension)
            new_engines[plugin_id] = engine

        self.engines = new_engines

    def _load_engine(self, extension):
        """ Load the Engine object for the given extension.

        Parameters
        ----------
        extension : Extension
            The extension object of interest.

        Returns
        -------
        engine : Engine
            The first Engine object declared by the extension.

        """
        workbench = self.workbench
        engines = extension.get_children(Engine)
        if extension.factory is not None and not engines:
            engine = extension.factory(workbench)
            if not isinstance(engine, Engine):
                msg = "extension '%s' created non-State of type '%s'"
                args = (extension.qualified_id, type(engine).__name__)
                raise TypeError(msg % args)
        else:
            engine = engines[0]

        return engine

    def _refresh_monitors(self):
        """ Refresh the list of known monitors.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(MONITORS_POINT)
        extensions = point.extensions
        if not extensions:
            self.monitors.clear()
            return

        new_monitors = {}
        old_monitors = self.monitors
        for extension in extensions:
            plugin_id = extension.plugin_id
            if plugin_id in old_monitors:
                monitor = old_monitors[plugin_id]
            else:
                monitor = self._load_monitor(extension)
            new_monitors[plugin_id] = monitor

        self.monitors = new_monitors

    def _load_monitor(self, extension):
        """ Load the Monitor object for the given extension.

        Parameters
        ----------
        extension : Extension
            The extension object of interest.

        Returns
        -------
        monitor : Monitor
            The first Monitor object declared by the extension.

        """
        workbench = self.workbench
        monitors = extension.get_children(Monitor)
        if extension.factory is not None and not monitors:
            monitor = extension.factory(workbench)
            if not isinstance(monitor, Monitor):
                msg = "extension '%s' created non-State of type '%s'"
                args = (extension.qualified_id, type(monitor).__name__)
                raise TypeError(msg % args)
        else:
            monitor = monitors[0]

        return monitor

    def _refresh_headers(self):
        """ Refresh the list of known headers.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(HEADERS_POINT)
        extensions = point.extensions
        if not extensions:
            self.headers.clear()
            return

        new_headers = {}
        old_headers = self.headers
        for extension in extensions:
            plugin_id = extension.plugin_id
            if plugin_id in old_headers:
                header = old_headers[plugin_id]
            else:
                header = self._load_monitor(extension)
            new_headers[plugin_id] = header

        self.headers = new_headers

    def _load_headers(self, extension):
        """ Load the Header object for the given extension.

        Parameters
        ----------
        extension : Extension
            The extension object of interest.

        Returns
        -------
        header : Header
            The first Header object declared by the extension.

        """
        workbench = self.workbench
        headers = extension.get_children(Header)
        if extension.factory is not None and not headers:
            header = extension.factory(workbench)
            if not isinstance(header, Header):
                msg = "extension '%s' created non-State of type '%s'"
                args = (extension.qualified_id, type(header).__name__)
                raise TypeError(msg % args)
        else:
            header = headers[0]

        return header

    def _refresh_checks(self):
        """ Refresh the list of known checks.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(CHECKS_POINT)
        extensions = point.extensions
        if not extensions:
            self.checks.clear()
            return

        new_checks = {}
        old_checks = self.checks
        for extension in extensions:
            plugin_id = extension.plugin_id
            if plugin_id in old_checks:
                check = old_checks[plugin_id]
            else:
                check = self._load_monitor(extension)
            new_checks[plugin_id] = check

        self.checks = new_checks

    def _load_checks(self, extension):
        """ Load the Check object for the given extension.

        Parameters
        ----------
        extension : Extension
            The extension object of interest.

        Returns
        -------
        check : Check
            The first Check object declared by the extension.

        """
        workbench = self.workbench
        checks = extension.get_children(Check)
        if extension.factory is not None and not checks:
            check = extension.factory(workbench)
            if not isinstance(check, Check):
                msg = "extension '%s' created non-State of type '%s'"
                args = (extension.qualified_id, type(check).__name__)
                raise TypeError(msg % args)
        else:
            check = checks[0]

        return check

    def _bind_observers(self):
        """ Setup the observers for the plugin.

        """
        workbench = self.workbench

        point = workbench.get_extension_point(ENGINES_POINT)
        point.observe('extensions', self._update_engines)

        point = workbench.get_extension_point(MONITORS_POINT)
        point.observe('extensions', self._update_monitors)

        point = workbench.get_extension_point(HEADERS_POINT)
        point.observe('extensions', self._update_headers)

        point = workbench.get_extension_point(CHECKS_POINT)
        point.observe('extensions', self._update_checks)

    def _unbind_observers(self):
        """ Remove the observers for the plugin.

        """
        workbench = self.workbench

        point = workbench.get_extension_point(ENGINES_POINT)
        point.unobserve('extensions', self._update_engines)

        point = workbench.get_extension_point(MONITORS_POINT)
        point.unobserve('extensions', self._update_monitors)

        point = workbench.get_extension_point(HEADERS_POINT)
        point.unobserve('extensions', self._update_headers)

        point = workbench.get_extension_point(CHECKS_POINT)
        point.unobserve('extensions', self._update_checks)

    def _update_engines(self, change):
        """
        """
        self._refresh_engines()

    def _update_monitors(self, change):
        """
        """
        self._refresh_monitors()

    def _update_headers(self, change):
        """
        """
        self._refresh_headers()

    def _update_checks(self, change):
        """
        """
        self._refresh_checks()
