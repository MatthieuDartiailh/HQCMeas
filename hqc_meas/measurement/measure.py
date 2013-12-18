# -*- coding: utf-8 -*-
from atom.api import (Atom, Instance, Bool)
from configobj import ConfigObj

from ..task_management.task_building import build_root
from ..task_management.task_saving import save_task
from .monitoring import MeasureMonitor
from ..tasks import RootTask

class Measure(Atom):
    """

    Attributes
    ----------
    is_running : bool
        Boolean indicating whether or not the measurement is running.
    root_task : instance(RootTask)
        `RootTask` instance representing the enqueued measure.
    monitor : instance(MeasureMonitor)
        Monitor which can be used to follow the measurement.
    use_monitor : bool
        Boolean indicating whether or not to use a monitor to follow the
        measure.

    """
    is_running = Bool(False)
    root_task = Instance(RootTask, ())
    monitor = Instance(MeasureMonitor, ())
    use_monitor = Bool(True)
    
    def save_measure(self, path):
        """
        """
        config = ConfigObj(path, indent_type = '    ')
        config['root_task'] = save_task(self.root_task, mode = 'config').dict()
        config['monitor'] = self.monitor.save_monitor_state()
        config.write()
    
    def load_measure(self, path):
        """
        """
        config = ConfigObj(path)
        if 'root_task' in config:
            self.root_task = build_root(mode = 'config',
                                        config = config['root_task'])
            self.monitor.load_monitor_state(config['monitor'])
        else:
            #Assume this a raw root_task file without name or monitor
            self.root_task = build_root(mode = 'config',
                                        config = config)
    
    def _observe_root_task(self, change):
        """
        """
        if 'oldvalue' in change:
            change['oldvalue'].unobserve('task_database.notifier',
                                             self.monitor.database_modified)
        self.monitor.clear_state()
        change['value'].task_database.observe('notifier',
                                             self.monitor.database_modified)
        database = change['value'].task_database
        self.monitor.database_entries = database.list_all_entries()
        self.monitor.refresh_monitored_entries()
        self.monitor.measure_name = ''

    def _observe_is_running(self, change):
        """
        """
        new = change['value']
        if new:
            self.monitor.status = 'RUNNING'