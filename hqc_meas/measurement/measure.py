# -*- coding: utf-8 -*-
from atom.api import (Atom, Instance, Bool, Dict, Unicode, Typed, Str)
from textwrap import fill
from configobj import ConfigObj

from ..task_management.saving import save_task
from ..task_management.building import build_root
from ..tasks.api import RootTask


class Measure(Atom):
    """

    """
    # Reference to the measure plugin managing this measure.
    plugin = Typed()

    # Name of the measure.
    name = Str()

    # Flag indicating the measure status.
    status = Str()

    # Root task holding the measure logic.
    root_task = Instance(RootTask, ())

    # Dict of active monitor for this measure.
    monitors = Dict(Unicode())

    # Dict of checks for this measure
    checks = Dict(Unicode())

    # Dict of header generators to call.
    headers = Dict(Unicode())

    # Dict to store useful runtime infos
    store = Dict(Str())

    use_monitor = Bool(True)

# TODO update to new logic
# =============================================================================
    def save_measure(self, path):
        """
        """
        config = ConfigObj(path, indent_type='    ')
        config['root_task'] = save_task(self.root_task, mode='config')
        config['monitor'] = self.monitor.save_monitor_state()
        config.write()

    # TODO make it a class method as it will need to request monitor, checks,
    # ... from the plugin.
    def load_measure(self, path):
        """
        """
        config = ConfigObj(path)
        if 'root_task' in config:
            self.root_task = build_root(mode='config',
                                        config=config['root_task'])
            self.monitor.load_monitor_state(config['monitor'])
        else:
            #Assume this a raw root_task file without name or monitor
            self.root_task = build_root(mode='config',
                                        config=config)

# =============================================================================

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
        full_report['internal'] = errors
        result = result and check

        if not internal_only:
            for id, check_method in self.checks.iteritems():
                check, errors = check_method(workbench, self.root_task)
                full_report[id] = errors
                result = result and check

        return result, full_report

    def collect_headers(self, workbench):
        """ Get all the contribution to the default_header.

        """
        header = ''
        for id, header_method in self.headers:
            header += ' ; ' + header_method(workbench)

        if header:
            header = fill(header[3:], 79)

        self.root_task.default_header = header

    def _observe_root_task(self, change):
        """ Observer ensuring that the monitors observe the right database.

        """
        monitors = self.monitors.values()
        if 'oldvalue' in change:
            old = change['oldvalue']
            # Stop observing the database (remove all handlers)
            old.unobserve('task_database.notifier')

        root = change['value']
        database = root.task_database
        for monitor in monitors:
            monitor.clear_state()
            root.task_database.observe('notifier',
                                       monitor.database_modified)

            monitor.database_entries = database.list_all_entries()
            monitor.refresh_monitored_entries()

    def _observe_is_running(self, change):
        """ Observer updating the monitors' status when the measure is run.

        """
        new = change['value']
        if new:
            for monitor in self.monitors:
                monitor.status = 'RUNNING'

    def _observe_name(self, change):
        """ Observer ensuring that the monitors know the name of the measure.

        """
        name = change['value']
        for monitor in self.monitors:
                monitor.name = name
