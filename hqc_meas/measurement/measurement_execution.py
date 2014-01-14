# -*- coding: utf-8 -*-
#==============================================================================
# module : measurement_execution.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
This module defines the tools used to run a measurement (ie a hierarchical
set of task).

:Contains:
    TaskProcess :
        Subclass of Process performing the measurement in another process to
        avoid being slowed down by the ui.
    TaskCheckModel :
        Simple UI used to diplay the results of a failed check.
    TaskHolder :
        Simple panel representing a measure in the queue of measure to be
        processed. Allow editing and monitor parametrisation.
    TaskHolderDialog :
        Simple dialog asking the user ot provide a name for the measure he is
        enqueuing and whether or not a monitor should be used.
    TaskExecutionControl :
        Store measurement in a queue of measures to be processed, take care of
        starting and communicating with the process performing the measure and
        handling user action (stopping single measure or whole process).
    TaskHolderHandler:
        Handler for `TaskHolder`.
    TaskExecutionControlHandler :.
        Handler for `TaskExecutionControl`.
"""
import os, logging, logging.config, warnings, sys
from logging.handlers import RotatingFileHandler
from multiprocessing import Process, Pipe
from multiprocessing.queues import Queue
from multiprocessing.synchronize import Event
from threading import Thread
from time import sleep

from atom.api import (Atom, Instance, Bool, Str, Value, ContainerList,
                      Dict, observe)
import enaml
from enaml.application import deferred_call

from.measure import Measure
from .monitoring import MeasureSpy, MeasureMonitor
from ..task_management.config import IniConfigTask
from ..log_facility import (StreamToLogRedirector, QueueLoggerThread)
with enaml.imports():
    from .monitoring_views import MonitorView
    from .execution_view import TaskCheckDisplay

class TaskProcess(Process):
    """Process taking care of performing the measures.

    When started this process sets up a logger redirecting all records to a
    queue. It then redirects stdout and stderr to the logging system. Then as
    long as there is measures to perform  it asks the main process to send it
    measures through a pipe. Upon reception of the `ConfigObj` object describing
    the measure it rebuilds it, set up a logger for that specific measure and if
    necessary starts a spy transmitting the value of all monitored entries to
    the main process. It finally run the checks of the measure and run it.
    It can be interrupted by setting an event and upon exit close the
    communication pipe and signal all listeners that it is closing.

    Parameters
    ----------
    pipe : double ended multiprocessing pipe
        Pipe used to communicate with the parent process which is transferring
        the measure to perform.
    log_queue : multiprocessing queue
        Queue in which all log records are sent to be procesed later in the main
        process.
    monitor_queue : multiprocessing queue
        Queue in which all the informations the user asked to monitor during the
        measurement are sent to be processed in the main process.
    task_stop : multiprocessing event
        Event set when the user asked the running measurement to stop.
    process_stop : multiprocessing event
        Event set when the user asked the process to stop.

    Attributes
    ----------
    meas_log_handler : log handler
        Log handler used to save the running measurement specific records.
    see `Parameters`

    Methods
    -------
    run():
        Method called when the new process starts.

    """

    def __init__(self, pipe, log_queue, monitor_queue, task_stop, process_stop):
        super(TaskProcess, self).__init__(name = 'MeasureProcess')
        self.task_stop = task_stop
        self.process_stop = process_stop
        self.pipe = pipe
        self.log_queue = log_queue
        self.monitor_queue = monitor_queue
        self.meas_log_handler = None

    def run(self):
        """Method called when the new process starts.

        For a complete description of the workflow see the class docstring.
        """
        self._config_log()
        # Ugly patch to avoid pyvisa complaining about missing filters
        warnings.simplefilter("ignore")

        # Redirecting stdout and stderr to the logging system.
        logger = logging.getLogger()
        redir_stdout = StreamToLogRedirector(logger)
        sys.stdout = redir_stdout
        logger.info('Logger parametrised')

        print 'Process running'
        while not self.process_stop.is_set():
            try:
                # Request a new measure to perform from the main process
                print 'Need task'
                self.pipe.send('Need task')

                # Get the answer
                self.pipe.poll(None)
                name, config, monitored_entries = self.pipe.recv()

                if config != 'STOP':
                    # If a real measurement was sent, build it.
                    task = IniConfigTask().build_task_from_config(config)
                    print 'Task built'

                    # There are entries in the database we are supposed to
                    # monitor start a spy to do it.
                    if monitored_entries is not None:
                        spy = MeasureSpy(self.monitor_queue, monitored_entries,
                                         task.task_database)

                    # Set up the logger for this specific measurement.
                    if self.meas_log_handler != None:
                        logger.removeHandler(self.meas_log_handler)
                        self.meas_log_handler.close()
                        self.meas_log_handler = None
                        
                    log_path = os.path.join(
                                        task.get_from_database('default_path'),
                                        name + '.log')
                    if os.path.isfile(log_path):
                        os.remove(log_path)
                    self.meas_log_handler = RotatingFileHandler(log_path,
                                                            mode = 'w',
                                                            maxBytes = 10**6,
                                                            backupCount = 10)
                    aux = '%(asctime)s | %(levelname)s | %(message)s'
                    formatter = logging.Formatter(aux)
                    self.meas_log_handler.setFormatter(formatter)
                    logger.addHandler(self.meas_log_handler)

                    # Clear the event signaling the task it should stop, pass it
                    # to the task and make the database ready.
                    self.task_stop.clear()
                    task.should_stop = self.task_stop
                    task.task_database.prepare_for_running()

                    # Perform the checks.
                    check = task.check(test_instr = True)
                    if check[0]:
                        print 'Check successful'
                        # Perform the measure
                        task.process()
                        self.pipe.send('Task processed')
                        if self.task_stop.is_set():
                            print 'Task interrupted'
                        else:
                            print 'Task processed'
                    else:
                        message = '\n'.join('{} : {}'.format(path, mes)
                                    for path, mes in check[1].iteritems())
                        logger.critical(message)

                    # If a spy was started kill it
                    if monitored_entries is not None:
                        spy.close()
                        del spy

            except IOError:
                pass

        # Clean up before closing.
        self.pipe.send('Closing')
        print 'Process shuting down'
        if self.meas_log_handler:
            self.meas_log_handler.close()
        self.log_queue.put_nowait(None)
        self.pipe.close()

    def _config_log(self):
        """Configuring the logger for the process. Sending all record to a
        multiprocessing queue.
        """
        config_worker = {
            'version': 1,
            'disable_existing_loggers': True,
            'handlers': {
                'queue': {
                    'class': 'hqc_meas.log_facility.QueueHandler',
                    'queue': self.log_queue,
                },
            },
            'root': {
                'level': 'DEBUG',
                'handlers': ['queue']
            },
        }
        logging.config.dictConfig(config_worker)
        if os.name == 'posix':
            # On POSIX, the setup logger will have been configured in the
            # parent process, but should have been disabled following the
            # dictConfig call.
            # On Windows, since fork isn't used, the setup logger won't
            # exist in the child, so it would be created and the message
            # would appear - hence the "if posix" clause.
            logger = logging.getLogger('setup')
            logger.critical('Should not appear, because of disabled logger ...')


class TaskCheckModel(Atom):
    """Simple dialog displaying the errors messages resulting from a failed
    check.

    Attributes
    ----------
    check_dict_result : dict(str, str)
        Dictionnary storing the path of the task in which a check failed and
        the associated message.
    name_to_path_dict : dict(str, str)
        Dictionnary mapping the name of the tasks in which a check failed to its
        path.
    selected_check : str
        Name of the task the user selected from `failed_check_list`.
    full_path : str
        Path of the selected task.
    message : str
        Message associated to the selected task.
    """
    check_dict_result = Dict(Str(), Str())
    name_to_path_dict = Dict(Str(), Str())

    selected_check = Str()
    full_path = Str()
    message = Str()

    def __init__(self, check_dict_result):
        super(TaskCheckModel, self).__init__()
        self.check_dict_result = check_dict_result
        self.name_to_path_dict = {key.rpartition('/')[-1] : key
                                    for key in self.check_dict_result.keys()}
        self.selected_check = self.name_to_path_dict.keys()[0]
        self.full_path = self.name_to_path_dict[self.selected_check]
        self.message = self.check_dict_result[self.full_path]

    @observe('selected_check')
    def _update(self, change):
        """Automatically set the `full_path` and `message` attribute when the
        user select a new failed check.
        """
        new = change['value']
        self.full_path = self.name_to_path_dict[new]
        self.message = self.check_dict_result[self.full_path]

class TaskExecutionControl(Atom):
    """Store measurement in a queue of measures to be processed, take care of
    starting and communicating with the process performing the measure and
    handling user action (stopping single measure or whole process).

    Attributes
    ----------
    running : bool
        Bool indicating whether or not the measurement process is running.
    task_stop : multiprocess.Event
        Event used to signal that the current measure should be stopped.
    process_stop : multiprocess.Event
        Event used to signal that the measurement process should be stopped.
    meas_holder : list(instance(Measure))
        List containing all the enqueued measure.
    process : instance(Process)
        Measurement process.
    log_thread : instance(Thread)
        Thread dedicated to handling the log records coming from the measurement
        process
    log_queue : multiprocessing queue
        Queue in which the log records of the measurement process are sent from
        the measurement process to the main process.
    monitor_queue :  multiprocessing queue
        Queue in which the value of the monitored parameters are sent from the
        measurement process to the main process.
    current_monitor : instance(MeasureMonitor)
        Monitor associated to the measurement being processed.
    pipe : multiprocessing double ended pipe
        Pipe used for communication between the two processus.

    Methods
    -------
    append_task(new_task):
        Method handling the enqueuing of a measurement in the queue.

    """

    running = Bool(False)
    task_stop = Instance(Event, ())
    process_stop = Instance(Event, ())

    meas_holder = ContainerList(Instance(Measure), [])

    process = Instance(Process)
    log_thread = Instance(Thread)
    log_queue = Instance(Queue, ())
    pipe = Value() #Instance of Connection but ambiguous when the OS is not known
    
    monitor_queue = Instance(Queue, ())
    current_monitor = Instance(MeasureMonitor)
    monitor_display = Instance(MonitorView)
    parent_widget = Instance(enaml.widgets.widget.Widget)
    

    def append_meas(self, new_meas):
        """Put a measure in the queue if it pass the tests.

        First the check method of the measure is called. If the tests pass,
        the user is asked to give a name to its measure (by default the name is
        'Meas"i"' where is the index of the measure in the queue), then he can
        choose what entries he wants to monitor during the measure which is then
        enqueued and finally saved in the default folder ('default_path'
        attributes of the `RootTask` describing the measure). Otherwise the list
        of the failed tests is displayed to the user.

        Parameters
        ----------
        new_task : instance(`RootTask`)
            Instance of `RootTask` representing the measure.

        Returns
        -------
        bool :
            True is the measure was successfully enqueued, False otherwise.
        """
        check = new_meas.root_task.check(
                    test_instr = not self.running)
        if check[0]:
            path = os.path.join(new_meas.root_task.default_path,
                                new_meas.monitor.measure_name + '_last_run.ini')
            new_meas.save_measure(path)
            meas = Measure()
            meas.load_measure(path)
            self.meas_holder.append(meas)

            return True
        else:
            TaskCheckDisplay(model = TaskCheckModel(check[1])).exec_()
            return False

    def _start_button_clicked(self, widget):
        """Handle the `start_button` being pressed.

        Clear the event `task_stop` and `process_stop`, create the pipe and
        the measurement process. Start then the log thread and then the process.
        Finally start the thread handling the communication with the measurement
        process.

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
        Thread(group = None, target = self._process_listerner).start()

    def _stop_all_button_clicked(self):
        """Handle the `stop_button` being pressed.

        Set the `process_stop` event and signal in the pipe that not more
        measurement will be sent. Then wait for the process and the log thread
        to terminate.

        """
        print 'Stopping process'
        self.process_stop.set()
        self.pipe.send((None, 'STOP', None))
        self.task_stop.set()
        self.process.join()
        self.log_thread.join()
        self.running = False

    def _stop_button_clicked(self):
        """Handle the `stop_task_button` being pressed by setting the
        `task_stop` event.
        """
        print 'Stopping task'
        self.task_stop.set()
        
    def _update_monitor_display_model(self, monitor):
        """
        """
        if not self.monitor_display:
            self.monitor_display = MonitorView(self.parent_widget,
                                               monitor = monitor)
        else:
            self.monitor_display.monitor = monitor
            
        if not self.monitor_display.visible:
            self.monitor_display.show()

    def _process_listerner(self):
        """Method called in a separated thread to handle communications with the
        measurement process.

        """
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
                        task.update_preferences_from_members()

                        if self.current_monitor:
                            self.current_monitor.stop()
                            self.current_monitor = None

                        self.current_monitor = monitor
                        deferred_call(setattr, monitor, 'status','RUNNING')
                        # Leave a chance to the system to update the display
                        sleep(0.1)
                            
                        if meas.use_monitor:
                            monitor.start(self.monitor_queue)
                            deferred_call(self._update_monitor_display_model,
                                          monitor)
                            self.pipe.send((name, task.task_preferences,
                                self.current_monitor.database_values.keys()))
                        else:
                            deferred_call(self.monitor_display.close)
                            self.pipe.send((name, task.task_preferences,
                                        None))
                            
                        print 'Measurement sent'

                    # If there is no measurement which can be sent, stop the
                    # measurement process.
                    else:
                        self.process_stop.set()
                        print 'The only task is the queue is being edited'
                        self.pipe.send(('', 'STOP',''))
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