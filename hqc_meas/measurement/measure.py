# -*- coding: utf-8 -*-
from atom.api import (Atom, Instance, Dict, Unicode, ForwardTyped, Str)
from configobj import ConfigObj
import logging

from ..tasks.api import RootTask


def measure_plugin():
    from .plugin import MeasurePlugin
    return MeasurePlugin


class Measure(Atom):
    """

    """
    #--- Public API -----------------------------------------------------------

    # Reference to the measure plugin managing this measure.
    plugin = ForwardTyped(measure_plugin)

    # Name of the measure.
    name = Str()

    # Flag indicating the measure status.
    status = Str()

    # Detailed information about the measure status.
    infos = Str()

    # Root task holding the measure logic.
    root_task = Instance(RootTask)

    # Dict of active monitor for this measure.
    monitors = Dict(Unicode())

    # Dict of checks for this measure
    checks = Dict(Unicode())

    # Dict of header generators to call.
    headers = Dict(Unicode())

    # Dict to store useful runtime infos
    store = Dict(Str())

    def save_measure(self, path):
        """ Save the measure as a ConfigObj object.

        Parameters
        ----------
        path : unicode
            Path of the file to which save the measure.

        """
        config = ConfigObj(path, indent_type='    ')
        core = self.plugin.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'hqc_meas.task_manager.save_task'
        config['root_task'] = {}
        config['root_task'].update(core.invoke_command(cmd,
                                                       {'task': self.root_task,
                                                        'mode': 'config'},
                                                       self))

        i = 0
        for id, monitor in self.monitors.iteritems():
            state = monitor.get_state()
            state['id'] = id
            config['monitor_{}'.format(i)] = state
            i += 1

        config['monitors'] = repr(i)
        config['checks'] = repr(self.checks.keys())
        config['headers'] = repr(self.headers.keys())
        config['name'] = self.name

        config.write()

    @classmethod
    def load_measure(cls, measure_plugin, path):
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
        measure.name = config['name']

        workbench = measure_plugin.workbench
        core = workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'hqc_meas.task_manager.build_root'
        kwarg = {'mode': 'config', 'config': config['root_task']}
        measure.root_task = core.invoke_command(cmd, kwarg, measure)

        for i in range(eval(config['monitors'])):
            monitor_config = config['monitor_{}'.format(i)]
            id = monitor_config.pop('id')
            try:
                monitor_decl = measure_plugin.monitors[id]
                monitor = monitor_decl.factory(workbench, monitor_decl,
                                               raw=True)
                monitor.set_state(monitor_config)
                measure.add_monitor(id, monitor)

            except KeyError:
                mess = 'Requested monitor not found : {}'.format(id)
                logger.warn(mess)

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
        root = self.root_task
        for monitor in self.monitors.values():
            root.task_database.observe('notifier',
                                       monitor.database_modified)

    def enter_running_state(self):
        """ Make the measure ready to run.

        """
        root = self.root_task
        for monitor in self.monitors.values():
            root.task_database.unobserve('notifier',
                                         monitor.database_modified)

    def add_monitor(self, id, monitor):
        """ Add a monitor, refresh its entries and connect observers.

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

        monitor.measure_name = self.name
        monitor.measure_status = self.status

        database = self.root_task.task_database
        self.monitors[id] = monitor
        entries = database.list_all_entries()
        monitor.refresh_monitored_entries(entries)
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
        monitor = self.monitors.pop(id)
        database.unobserve('notifier', monitor.database_modified)

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

    #--- Private API ----------------------------------------------------------

    def _observe_root_task(self, change):
        """ Observer ensuring that the monitors observe the right database.

        """
        monitors = self.monitors.values()
        if 'oldvalue' in change:
            old = change['oldvalue']
            # Stop observing the database (remove all handlers)
            old.task_database.unobserve('notifier')

        root = change['value']
        database = root.task_database
        for monitor in monitors:
            monitor.clear_state()
            root.task_database.observe('notifier',
                                       monitor.database_modified)

            monitor.refresh_monitored_entries(database.list_all_entries())

    def _observe_status(self, change):
        """ Observer updating the monitors' status when the measure is run.

        """
        new = change['value']
        if new:
            for monitor in self.monitors.values():
                monitor.measure_status = new

    def _observe_name(self, change):
        """ Observer ensuring that the monitors know the name of the measure.

        """
        name = change['value']
        for monitor in self.monitors.values():
                monitor.measure_name = name
