# -*- coding: utf-8 -*-
# =============================================================================
# module : measure.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from atom.api import (Atom, Instance, Dict, Unicode, ForwardTyped, Str)
from configobj import ConfigObj
import logging

from hqc_meas.tasks.api import RootTask
from hqc_meas.utils.configobj_ops import include_configobj


def measure_plugin():
    from .plugin import MeasurePlugin
    return MeasurePlugin


class Measure(Atom):
    """

    """
    # --- Public API ----------------------------------------------------------

    #: Reference to the measure plugin managing this measure.
    plugin = ForwardTyped(measure_plugin)

    #: Flag indicating the measure status.
    status = Str()

    #: Detailed information about the measure status.
    infos = Str()

    #: Path to the last file in which that measure was saved.
    path = Unicode()

    #: Root task holding the measure logic.
    root_task = Instance(RootTask)

    #: Dict of active monitor for this measure.
    monitors = Dict(Unicode())

    #: Dict of checks for this measure
    checks = Dict(Unicode())

    #: Dict of header generators to call.
    headers = Dict(Unicode())

    #: Dict to store useful runtime infos
    store = Dict(Str())

    def save_measure(self, path):
        """ Save the measure as a ConfigObj object.

        Parameters
        ----------
        path : unicode
            Path of the file to which save the measure.

        """
        config = ConfigObj(indent_type='    ')
        core = self.plugin.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'hqc_meas.task_manager.save_task'
        config['root_task'] = {}
        task_prefs = core.invoke_command(cmd, {'task': self.root_task,
                                               'mode': 'config'}, self)
        include_configobj(config['root_task'], task_prefs)

        i = 0
        for id, monitor in self.monitors.iteritems():
            state = monitor.get_state()
            state['id'] = id
            config['monitor_{}'.format(i)] = state
            i += 1

        config['monitors'] = repr(i)
        config['checks'] = repr(self.checks.keys())
        config['headers'] = repr(self.headers.keys())
        # Stays here for backwards compatibility
        config['name'] = self.root_task.meas_name

        with open(path, 'w') as f:
            config.write(f)

        self.path = path

    @classmethod
    def load_measure(cls, measure_plugin, path, build_dep=None):
        """ Build a measure from a ConfigObj file.

        Parameters
        ----------
        measure_plugin : MeasurePlugin
            Instance of the MeasurePlugin storing all declarations.

        path : unicode
            Path of the file from which to load the measure.

        """
        logger = logging.getLogger(__name__)
        measure = cls()
        config = ConfigObj(path)
        measure.plugin = measure_plugin
        measure.path = path

        workbench = measure_plugin.workbench
        core = workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'hqc_meas.task_manager.build_root'
        kwarg = {'mode': 'config', 'config': config['root_task'],
                 'build_dep': build_dep}
        measure.root_task = core.invoke_command(cmd, kwarg, measure)
        measure.root_task.meas_name = config['name']
        database = measure.root_task.task_database
        entries = database.list_all_entries(values=True)

        for i in range(eval(config['monitors'])):
            monitor_config = config['monitor_{}'.format(i)]
            id = monitor_config.pop('id')
            try:
                monitor_decl = measure_plugin.monitors[id]

            except KeyError:
                mess = 'Requested monitor not found : {}'.format(id)
                logger.warn(mess)

            try:
                monitor = monitor_decl.factory(monitor_decl, workbench,
                                               raw=True)
                monitor.set_state(monitor_config, entries)
                # Don't refresh as it has been done already
                measure.add_monitor(id, monitor, False)

            except Exception:
                mess = 'Failed to restore monitor : {}'.format(id)
                logger.warn(mess, exc_info=True)

        for check_id in eval(config['checks']):
            try:
                check = measure_plugin.checks[check_id]
                measure.checks[check_id] = check

            except KeyError:
                mess = 'Requested check not found : {}'.format(check_id)
                logger.warn(mess)

        for header_id in eval(config['headers']):
            try:
                header = measure_plugin.headers[header_id]
                measure.headers[header_id] = header

            except KeyError:
                mess = 'Requested header not found : {}'.format(header_id)
                logger.warn(mess)

        return measure

    def run_checks(self, workbench, test_instr=False, internal_only=False):
        """ Run the checks to see if everything is ok.

        First the task specific checks are run, and then the ones contributed
        by plugins.

        Returns
        -------
        result : bool
            Bool indicating whether or not the tests passed.

        errors : dict
            Dictionary containing the failed check organized by id ('internal'
            or plugin id).

        """
        result = True
        full_report = {}
        check, errors = self.root_task.check(test_instr=test_instr)
        if errors:
            full_report[u'internal'] = errors
        result = result and check

        if not internal_only:
            for id, check_decl in self.checks.iteritems():
                check, errors = check_decl.perform_check(workbench,
                                                         self.root_task)
                if errors:
                    full_report[id] = errors
                result = result and check

        return result, full_report

    def enter_edition_state(self):
        """ Make the the measure ready to be edited

        """
        database = self.root_task.task_database
        for monitor in self.monitors.values():
            if not database.has_observer('notifier',
                                         monitor.database_modified):
                database.observe('notifier', monitor.database_modified)

    def enter_running_state(self):
        """ Make the measure ready to run.

        """
        database = self.root_task.task_database
        for monitor in self.monitors.values():
            if database.has_observer('notifier', monitor.database_modified):
                database.unobserve('notifier', monitor.database_modified)

    def add_monitor(self, id, monitor, refresh=True):
        """ Add a monitor, connect observers.

        Parameters
        ----------
        id : unicode
            Id of the monitor being added.

        monitor : BaseMonitor
            Instance of the monitor being added.

        """
        if id in self.monitors:
            logger = logging.getLogger(__name__)
            logger.warn('Monitor already present : {}'.format(id))
            return

        monitor.measure_name = self.root_task.meas_name +\
            self.root_task.meas_id
        monitor.measure_status = self.status

        database = self.root_task.task_database
        # Work around not having a container dict
        monitors = self.monitors.copy()
        monitors[id] = monitor
        self.monitors = monitors
        if refresh:
            database_entries = database.list_all_entries(values=True)
            monitor.refresh_monitored_entries(database_entries)
        database.observe('notifier', monitor.database_modified)

    def remove_monitor(self, id):
        """ Remove a monitor and disconnect observers.

        Parameters
        ----------
        id : unicode
            Id of the monitor to remove.

        """
        if id not in self.monitors:
            logger = logging.getLogger(__name__)
            logger.warn('Monitor is not present : {}'.format(id))
            return

        database = self.root_task.task_database
        # Workaround the missing ContainerDict
        monitors = self.monitors.copy()
        monitor = monitors.pop(id)
        database.unobserve('notifier', monitor.database_modified)
        self.monitors = monitors

    def collect_headers(self, workbench):
        """ Set the default_header of the root task using all contributions.

        """
        header = ''
        for id, header_decl in self.headers.iteritems():
            header += '\n' + header_decl.build_header(workbench)

        self.root_task.default_header = header.strip()

    def collect_entries_to_observe(self):
        """ Get all the entries the monitors ask to be notified about.

        Returns
        -------
        entries : list
            List of the entries the engine will to observe.

        """
        entries = []
        for monitor in self.monitors.values():
            entries.extend(monitor.database_entries)

        return list(set(entries))

    # --- Private API ---------------------------------------------------------

    def _observe_root_task(self, change):
        """ Observer ensuring that the monitors observe the right database.

        """
        monitors = self.monitors.values()
        if 'oldvalue' in change:
            old = change['oldvalue']
            # Stop observing the database (remove all handlers)
            old.task_database.unobserve('notifier')
            old.unobserve('meas_name', self._update_monitor_name)

        root = change['value']
        database = root.task_database
        root.observe('meas_name', self._update_monitor_name)
        for monitor in monitors:
            monitor.clear_state()
            root.task_database.observe('notifier',
                                       monitor.database_modified)

            database_entries = database.list_all_entries(values=True)
            monitor.refresh_monitored_entries(database_entries)

    def _observe_status(self, change):
        """ Observer updating the monitors' status when the measure is run.

        """
        new = change['value']
        if new:
            for monitor in self.monitors.values():
                monitor.measure_status = new

    def _update_monitor_name(self, change):
        """ Observer ensuring that the monitors know the name of the measure.

        """
        name = change['value']
        for monitor in self.monitors.values():
                monitor.measure_name = name
