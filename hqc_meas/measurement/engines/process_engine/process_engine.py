# -*- coding: utf-8 -*-
#==============================================================================
# module : process_engine.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import Typed, Value, Tuple
from enaml.workbench.api import Workbench
from multiprocessing import Pipe
from multiprocessing.queues import Queue
from multiprocessing.synchronize import Event
from threading import Thread
from threading import Event as tEvent
import logging

from hqc_meas.log_system.tools import QueueLoggerThread
from hqc_meas.tasks.tools.walks import flatten_walk

from ..base_engine import BaseEngine
from ..tools import ThreadMeasureMonitor
from .subprocess import TaskProcess


class ProcessEngine(BaseEngine):
    """ An engine executing the measurement it is sent in a different process.

    """
    # Reference to the workbench got at __init__
    workbench = Typed(Workbench)

    # Interprocess event used to stop the subprocess current measure.
    _meas_stop = Typed(Event, ())

    # Interprocess event used to stop the subprocess.
    _stop = Typed(Event, ())

    # Flag signaling that a forced exit has been requested
    _force_stop = Value(tEvent())

    # Flag indicating the communication thread it can send the next measure.
    _starting_allowed = Value(tEvent())

    # Temporary tuple to store the data to be sent to the process when a
    # new measure is ready.
    _temp = Tuple()

    # Current subprocess.
    _process = Typed(TaskProcess)

    # Connection used to send and receive messages about execution (type
    # ambiguous when the OS is not known)
    _pipe = Value()

    # Thread in charge of transferring measure to the process.
    _com_thread = Typed(Thread)

    # Inter-process queue used by the subprocess to transmit its log records.
    _log_queue = Typed(Queue, ())

    # Thread in charge of collecting the log message coming from the
    # subprocess.
    _log_thread = Typed(Thread)

    # Inter-process queue used by the subprocess to send the values of the
    # observed database entries.
    _monitor_queue = Typed(Queue, ())

    # Thread in charge of collecting the values of the observed database
    # entries.
    _monitor_thread = Typed(Thread)

    def prepare_to_run(self, name, root, monitored_entries):
        # Get all the tasks classes we need to rebuild the measure in the
        # process.
        walk = root.walk(['task_class'])
        task_names = flatten_walk(walk)

        # Get core plugin to request tasks.
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.task_manager.tasks_request'
        task_classes, _ = core.invoke_command(com, {'tasks': task_names,
                                                    'use_class_names': True},
                                              self)

        # Gather all runtime dependencies in a single dict.
        runtimes = root.run_time
        runtimes['task_classes', task_classes]

        # Get ConfigObj describing measure.
        root.update_preferences_from_members()
        config = root.task_preferences

        # Make infos tuple to send to the subprocess.
        self._temp = (name, config, runtimes, monitored_entries)

        # Clear all the flags.
        self._meas_stop.clear()
        self._stop.clear()
        self._force_stop.clear()

        # If the process does not exist or is dead create a new one.
        if not self._process or not self._process.is_alive():
            self._pipe, process_pipe = Pipe()
            self._process = TaskProcess(process_pipe,
                                        self._log_queue,
                                        self._monitor_queue,
                                        self._meas_stop,
                                        self._stop)
            self._process.daemon = True

            self._log_thread = QueueLoggerThread(self._log_queue)
            self._log_thread.daemon = True

            self._monitor_thread = ThreadMeasureMonitor(self,
                                                        self._monitor_queue)
            self._monitor_thread.daemon = True

    def run(self):
        if not self._process.is_alive():
            # Starting monitoring threads.
            self._log_thread.start()
            self._monitor_thread.start()

            # Start process.
            self._process.start()
            self.active = True

            # Start main communication thread.
            self._com_thread = Thread(group=None,
                                      target=self._process_listener)
            self._com_thread.start()

        self._starting_allowed.set()

    def stop(self):
        self._meas_stop.set()

    def exit(self):
        self._stop.set()
        # Everything else handled by the _com_thread.

    def force_stop(self):
        # Just in case the user calls this directly. Will signal all threads to
        # stop (save _com_thread).
        self._stop.set()

        # Set _force_stop to stop _com_thread.
        self._force_stop.set()

        # Terminate the process and make sure all threads stopped properly.
        self._process.terminate()
        self._log_thread.join()
        self._monitor_thread.join()
        self._com_thread.join()
        self.active = False
        self.done = ('INTERRUPTED', 'The user forced the system to stop')

        # Discard the queues as they may have been corrupted when the process
        # was terminated.
        self._log_queue = Queue()
        self._monitor_queue = Queue()

    def force_exit(self):
        self.force_stop()

    def _process_listener(self):
        """ Handle the communications with the worker process.

        Executed in a different thread.

        """
        logger = logging.getLogger(__name__)
        logger.info('Starting listener')

        while not self._pipe.poll(2):
            if not self._process.is_alive():
                self.done = ('FAILED', 'Subprocess failed to start')
                self._stop.set()
                self._cleanup(process=False)
                return

        mess = self._pipe.recv()
        if mess != 'READY':
            self.done = ('FAILED', 'Subprocess failed to start')
            self._cleanup()
            return

        # Infinite loop waiting for measure.
        while not self._stop.is_set():

            # Wait for measure and check for stopping.
            while not self._starting_allowed.wait(2):
                if self._stop.is_set():
                    self._cleanup()
                    return

            # Send the measure.
            self.pipe.send(self._temp)

            # Empty _temp and reset flag.
            self._temp = None
            self._starting_allowed.clear()

            logger.info('Measurement sent')

            # Wait for the process to finish the measure and check it has not
            # been killed.
            while not self._pipe.poll(1):
                if self._force_stop.is_set():
                    self._cleanup()
                    return

            # Here get message from process and react
            meas_status, int_status, mess = self._pipe.recv()

            self.done = (meas_status, mess)
            if int_status == 'STOPPING':
                self._cleanup()

    def _cleanup(self, process=True):
        """ Helper method taking care of making sure that everybody stops.

        Parameters
        ----------
        process : bool
            Wether to join the worker process. Used when the process has been
            termintaed abruptly.

        """
        self._pipe.close()
        if process:
            self._process.join()
        self._log_thread.join()
        self._monitor_thread.join()
        self.active = False
