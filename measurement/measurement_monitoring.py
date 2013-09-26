# -*- coding: utf-8 -*-

from threading import Thread
from traits.api import (HasTraits, Set, Instance, Any, Str, List, Dict)
from traitsui.api import (View, UItem, TabularEditor, SetEditor, HGroup, Label,
                          TitleEditor, VGroup)
from traitsui.tabular_adapter import TabularAdapter
from pyface.api import GUI
from time import sleep

from .task_management.tasks.tools.task_database import TaskDatabase

class MeasureSpy(HasTraits):
    """
    """
    observed_entries = Set
    observed_database = Instance(TaskDatabase)

    def __init__(self, queue, observed_entries, observed_database):
        super(MeasureSpy, self).__init__()
        self.queue = queue
        self.observed_entries = set(observed_entries)
        self.observed_database = observed_database
        self.on_trait_change(self.enqueue_update, 'observed_database:notifier')

    def enqueue_update(self, new):
        if new[0] in self.observed_entries:
            self.queue.put_nowait(new)

    def close(self):
        self.queue.put((None,None))

class ThreadMeasureMonitor(Thread):
    """
    """
    def __init__(self, queue, monitor):
        super(ThreadMeasureMonitor, self).__init__()
        self.queue = queue
        self.monitor = monitor

    def run(self):
        while True:
            news = self.queue.get()
            if news != (None, None):
                self.monitor.map_news(news)
            else:
                break

class MonitoredPairAdapter(TabularAdapter):

    columns = [('Name', 'name'), ('Value', 'value') ]

class MonitoredPair(HasTraits):
    """
    """
    name = Str
    value = Any

class MeasureMonitor(HasTraits):
    """
    """
    monitored_pairs = List(Instance(MonitoredPair))
    monitored_map = Dict(Str, Instance(MonitoredPair))
    monitored_entries = List(Str)
    monitoring_thread = Instance(Thread)
    status = Str
    measure_name = Str

    monitoring_view = View(
                        VGroup(
                            UItem('measure_name', editor = TitleEditor()),
                            HGroup(Label('STATUS'),
                                   UItem('status', style = 'readonly')),
                            UItem('monitored_pairs',
                                  editor = TabularEditor(
                                              adapter = MonitoredPairAdapter(),
                                                operations = ['move'],
                                                selectable = False,
                                                editable = False,
                                                auto_update = True,
                                                auto_resize = True,
                                                drag_move = True),
                                ),
                            ),
                        title = 'Measurement monitor',
                        resizable = True, width = 300,
                        )

    def define_monitored_entries(self, database, parent = None):
        """
        """
        possible_entries_path = database.list_all_entries()
        possible_entries_map = {path.rpartition('/')[-1] : path
                                    for path in possible_entries_path}
        possible_entries = possible_entries_map.keys()
        self.monitored_entries = [entry for entry in possible_entries
                                    if 'array' not in entry]
        view = View(
                UItem('monitored_entries',
                      editor = SetEditor(values = possible_entries,
                                     can_move_all = True,
                                     left_column_title = 'Database entries',
                                     right_column_title = 'Monitored entries',
                                     ),
                    ),
                kind = 'modal', buttons = ['OK', 'Cancel'],
                title = 'Select the database entries to monitor',
                )

        ui = self.edit_traits(view, parent = parent)
        if ui.result:
            self.monitored_entries.sort()
            self.monitored_map = {possible_entries_map[entry] :
                                    MonitoredPair(name = entry) for
                                    entry in self.monitored_entries}
            self.monitored_pairs = [self.monitored_map[
                                                possible_entries_map[entry]]
                                            for entry in self.monitored_entries]
        return ui.result

    def map_news(self, news):
        """
        """
        self.monitored_map[news[0]].value = news[1]

    def start_monitor(self, queue):
        """
        """
        self.monitoring_thread = ThreadMeasureMonitor(queue, self)
        self.monitoring_thread.start()

    def stop_monitor(self):
        """
        """
        self.monitoring_thread.join()
        GUI.invoke_later(self.ui.dispose)

    def open_window(self, parent = None):
        """
        """
        GUI.invoke_later(self._open_window, parent)
        sleep(0.2)

    def _open_window(self, parent = None):
        """
        """
        self.ui = self.edit_traits(view = 'monitoring_view', parent = parent)
