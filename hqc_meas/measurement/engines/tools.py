# -*- coding: utf-8 -*-
#==============================================================================
# module : tools.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from threading import Thread
from multiprocessing.queues import Queue
from atom.api import Atom, Coerced, Typed
from hqc_meas.tasks.tools.task_database import TaskDatabase


class MeasureSpy(Atom):

    """
    """
    observed_entries = Coerced(set)
    observed_database = Typed(TaskDatabase)
    queue = Typed(Queue)

    def __init__(self, queue, observed_entries, observed_database):
        super(MeasureSpy, self).__init__()
        self.queue = queue
        self.observed_entries = set(observed_entries)
        self.observed_database = observed_database
        self.observed_database.observe('notifier', self.enqueue_update)

    def enqueue_update(self, change):
        new = change['value']
        if new[0] in self.observed_entries:
            self.queue.put_nowait(new)

    def close(self):
        self.queue.put((None, None))


class ThreadMeasureMonitor(Thread):

    """
    """

    def __init__(self, queue, monitor):
        super(ThreadMeasureMonitor, self).__init__()
        self.queue = queue
        self.monitor = monitor

    def run(self):
        while True:
            try:
                pass
#                news = self.queue.get()
#                if news != (None, None):
#                    deferred_call(self.monitor.map_news, news)
#                else:
#                    break
            except Queue.Empty:
                continue
