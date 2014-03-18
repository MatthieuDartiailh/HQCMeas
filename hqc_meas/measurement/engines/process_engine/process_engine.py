# -*- coding: utf-8 -*-
#==============================================================================
# module : process_engine.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import Typed, Instance, Bool, Value
from multiprocessing import Pipe
from multiprocessing.queues import Queue
from multiprocessing.synchronize import Event
from threading import Thread
from time import sleep

from ..base_engine import BaseEngine
from .subprocess import TaskProcess


class ProcessEngine(BaseEngine):
    """

    """
    workbench = Typed()

    running = Bool(False)
    task_stop = Instance(Event, ())
    process_stop = Instance(Event, ())

    process = Typed(TaskProcess)
    log_thread = Instance(Thread)
    log_queue = Instance(Queue, ())
    # Instance of Connection but ambiguous when the OS is not known
    pipe = Value()

    monitor_queue = Instance(Queue, ())

    # TODO will go somewhere
    def totot(self):
        """Handle the `start_button` being pressed.

        Clear the event `task_stop` and `process_stop`, create the pipe
        and the measurement process. Start then the log thread and then
        the process. Finally start the thread handling the communication
        with the measurement process.

        """
        if not self.parent_widget:
            self.parent_widget = widget
        print 'Starting process'
        self.task_stop.clear()
        self.process_stop.clear()
        self.pipe, process_pipe = Pipe()
        self.process = TaskProcess(process_pipe,
                                   self.log_queue,
                                   self.monitor_queue,
                                   self.task_stop,
                                   self.process_stop)
        self.log_thread = QueueLoggerThread(self.log_queue)
        self.log_thread.daemon = True
        self.log_thread.start()

        self.process.start()
        self.running = True
        Thread(group=None, target=self._process_listerner).start()

    def prepare_to_run(self, root, monitored_entries):
        """
        """
        mes = cleandoc('''''')
        raise NotImplementedError(mes)

    def run(self):
        """
        """
        mes = cleandoc('''''')
        raise NotImplementedError(mes)

    def stop(self):
        """
        """
        mes = cleandoc('''''')
        raise NotImplementedError(mes)

    def exit(self):
        """
        """
        mes = cleandoc('''''')
        raise NotImplementedError(mes)

    def force_stop(self):
        """
        """
        mes = cleandoc('''''')
        raise NotImplementedError(mes)

    def force_exit(self):
        """
        """
        mes = cleandoc('''''')
        raise NotImplementedError(mes)

    def _process_listerner(self):
        """Method called in a separated thread to handle communications with
        the measurement process."""
        print 'Starting listener'
        meas = None
        while not self.process_stop.is_set():
            self.pipe.poll(None)
            mess = self.pipe.recv()
            print 'Message received : {}'.format(mess)
            if mess == 'Need task':
                if self.meas_holder:
                    i = 0
                    task = None
                    # Look for a measure not being currently edited.
                    while i < len(self.meas_holder):
                        aux = self.meas_holder[i]
                        if aux.monitor.status == 'EDITING' or aux == meas:
                            i += 1
                            continue
                        else:
                            meas = self.meas_holder[i]
                            task = meas.root_task
                            monitor = meas.monitor
                            name = meas.monitor.measure_name
                            break

                    # If one is found, stop the old monitor, if necessary start
                    # a new one and send the measure in the pipe.
                    if task is not None:
                        meas.is_running = True
                        # TODO here should get default header from panel

                        task.update_preferences_from_members()

                        # Here must walk the task tree to find the used profile
                        # and ask a potential control panel to release the instrs
                        # it is currently holding
                        aux = task.walk(['selected_profile'])
                        profiles = extract_profiles(aux)
                        # TODO pass this to the control panel

                        if self.current_monitor:
                            self.current_monitor.stop()
                            self.current_monitor = None

                        self.current_monitor = monitor
                        deferred_call(setattr, monitor, 'status', 'RUNNING')
                        # Leave a chance to the system to update the display
                        sleep(0.05)

                        monitor_values = None
                        if meas.use_monitor:
                            monitor.start(self.monitor_queue)
                            deferred_call(self._update_monitor_display_model,
                                          monitor)
                            monitor_values = \
                                self.current_monitor.database_values.keys()
                        else:
                            deferred_call(self.monitor_display.close)

                        self.pipe.send((name, task.task_preferences,
                                        monitor_values))

                        print 'Measurement sent'

                    # If there is no measurement which can be sent, stop the
                    # measurement process.
                    else:
                        self.process_stop.set()
                        print 'The only task is the queue is being edited'
                        self.pipe.send(('', 'STOP', ''))
                        self.pipe.poll(None)
                        self.pipe.close()
                        self.process.join()
                        self.log_thread.join()
                        self.running = False
                        break

                # If there is no measurement in the queue, stop the
                # measurement process.
                else:
                    self.process_stop.set()
                    print 'All measurements have been sent'
                    self.pipe.send((None, 'STOP', None))
                    self.pipe.poll(None)
                    self.pipe.close()
                    self.process.join()
                    self.log_thread.join()
                    self.running = False
                    break

            elif mess == 'Task processed':
                deferred_call(self.meas_holder.remove, meas)
                sleep(0.1)

            # If the measurement process sent a different message,
            # it means it will stop so we can clean up.
            else:
                self.pipe.close()
                self.process.join()
                self.log_thread.join()
                self.running = False
                break

        # Upon exit close the monitor if it is still opened.
        if self.current_monitor:
            deferred_call(setattr, self.current_monitor, 'status', 'STOPPED')
            self.current_monitor.stop()