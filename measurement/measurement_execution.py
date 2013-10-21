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
    TaskCheckDisplay :
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
import sys, os, logging, logging.config, warnings
from logging.handlers import RotatingFileHandler
from multiprocessing import Process, Pipe, Queue
from multiprocessing.synchronize import Event
from threading import Thread
from traits.api import (HasTraits, Instance, Button, Bool, Str, Any,
                        List, Dict, on_trait_change)
from traitsui.api import (View, UItem, HGroup, VGroup, Handler,
                        ListInstanceEditor, Item, Label, ListStrEditor,
                        TextEditor, TitleEditor)
from .task_management.tasks import RootTask
from .measurement_edition import MeasurementEditor
from .measurement_monitoring import MeasureSpy, MeasureMonitor
from .task_management.config import IniConfigTask
from .log.log_facility import (StreamToLogRedirector, QueueLoggerThread)

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

            except Exception as e:
                logger.critical(e.message, exc_info = True)

        # Clean up before closing.
        self.pipe.send('Closing')
        print 'Process shuting down'
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
                    'class': 'measurement.log.log_facility.QueueHandler',
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


class TaskCheckDisplay(HasTraits):
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
    failed_check_list : list(str)
        List of the name of the task in which a check failed.
    selected_check : str
        Name of the task the user selected from `failed_check_list`.
    full_path : str
        Path of the selected task.
    message : str
        Message associated to the selected task.
    """
    check_dict_result = Dict(Str, Str)

    name_to_path_dict = Dict(Str, Str)
    failed_check_list = List(Str)

    selected_check = Str
    full_path = Str
    message = Str

    view = View(
            HGroup(
                UItem('failed_check_list',
                      editor = ListStrEditor(selected = 'selected_check',
                                             editable = False),
                    width = 300),
                VGroup(
                    UItem('full_path', editor = TitleEditor(), width = 500),
                    UItem('message', editor = TextEditor(multi_line = True,
                                          read_only = True)),
                    ),
                ),
            kind = 'live',
            title = 'Errors in the check'
            )

    def __init__(self, check_dict_result):
        super(TaskCheckDisplay, self).__init__()
        self.check_dict_result = check_dict_result
        self.name_to_path_dict = {key.rpartition('/')[-1] : key
                                    for key in self.check_dict_result.keys()}
        self.failed_check_list = self.name_to_path_dict.keys()
        self.seleted_check = self.failed_check_list[0]
        self.full_path = self.name_to_path_dict[self.seleted_check]
        self.message = self.check_dict_result[self.full_path]
        self.edit_traits()

    @on_trait_change('selected_check')
    def _update(self, new):
        """Automatically set the `full_path` and `message` attribute when the
        user select a new failed check.
        """
        self.full_path = self.name_to_path_dict[new]
        self.message = self.check_dict_result[self.full_path]

class TaskHolderHandler(Handler):
    """Simple handler connected to a `TaskHolder` instance.
    """

    def object_edit_button_changed(self, info):
        """Open a measurement editor when the user click the edit button and
        take care of updating the ini file in which the measurement info are
        stored.

        """
        model = info.object
        meas_editor = MeasurementEditor(root_task = model.root_task,
                                        is_new_meas = False)
        model.status = 'EDITING'
        default_path = meas_editor.root_task.default_path
        meas_editor.edit_traits(parent = info.ui.control,
                                kind = 'livemodal',
                                )

        task = model.root_task = meas_editor.root_task
        path = os.path.join(default_path,
                                model.name + '.ini')
        if task.default_path == default_path:
            with open(path, 'w') as f:
                task.update_preferences_from_traits()
                task.task_preferences.write(f)
        else:
            os.remove(path)
            path = os.path.join(task.default_path,
                                model.name + '.ini')
            with open(path, 'w') as f:
                task.update_preferences_from_traits()
                task.task_preferences.write(f)

        model.status = 'READY'

    def object_edit_monitor_changed(self, info):
        """Open a monitored entries editor when the user click the edit monitor
        button.

        """
        model = info.object
        model.monitor.define_monitored_entries(model.root_task.task_database,
                                               parent = info.ui.control)

class TaskHolder(HasTraits):
    """Panel representing a measurement in the queue of measurement to be
    performed.

    Attributes
    ----------
    name : str
        Name of the measurement associated with that panel
    status : str
        Current status of the measurement ('READY', 'EDITING', 'RUNNING')
    edit_button : button
        Button to open an editor to modify the enqueued measures.
    is_running : bool
        Boolean indicating whether or not the measurement is running.
    root_task : instance(RootTask)
        `RootTask` instance representing the enqueued measure.
    monitor : instance(MeasureMonitor)
        Monitor which could be used to follow the measurement.
    use_monitor : bool
        Boolean indicating whether or not to use a monitor to follow the
        measure.
    edit_monitor : button
        Button to open an editor to modify the monitored entries.

    """
    name = Str
    status = Str('READY')
    edit_button = Button('Edit')
    is_running = Bool(False)
    root_task = Instance(RootTask)

    monitor = Instance(MeasureMonitor)
    use_monitor = Bool(True)
    edit_monitor = Button('Edit monitor')

    traits_view = View(
                    VGroup(
                        UItem('name', style = 'readonly'),
                        VGroup(
                            UItem('status', style = 'readonly',
                                  resizable = True),
                            show_border = True,
                            label = 'Status',
                            ),
                        HGroup(
                            UItem('edit_button',
                                  enabled_when = 'not is_running'),
                            Item('use_monitor',
                                  enabled_when = 'not is_running'),
                            UItem('edit_monitor',
                                  enabled_when = 'not is_running',
                                  visible_when = 'use_monitor'),
                            ),
                        show_border = True,
                        label = 'Measure',
                        ),
                    handler = TaskHolderHandler(),
                    resizable = False,
                    height = -50,
                    )
    def __init__(self, *args, **kwargs):
        super(TaskHolder, self).__init__(*args, **kwargs)
        self.monitor = MeasureMonitor(measure_name = kwargs.get('name',''))

    def _is_running_changed(self, new):
        """
        """
        if new:
            self.status = 'RUNNING'

class TaskHolderDialog(HasTraits):
    """Simple dialog asking the user ot provide a name for the measure he is
    enqueuing and whether or not a monitor should be used.

    """
    name = Str
    use_monitor = Bool(True)

    traits_view = View(
                    VGroup(
                        UItem('name'),
                        HGroup(
                            Label('Use monitor'),
                            UItem('use_monitor'),
                            ),
                       ),
                   buttons = ['OK', 'Cancel'],
                   title = 'Enter a name for your measurement',
                   width = 200, kind = 'modal')

class TaskExecutionControlHandler(Handler):
    """Handler for `TaskExecutionControl`.
    """
    def closed(self, info, is_ok):
        if info.object.current_monitor:
            if hasattr(info.object.current_monitor, 'ui'):
                info.object.current_monitor.ui.dispose()

class TaskExecutionControl(HasTraits):
    """Store measurement in a queue of measures to be processed, take care of
    starting and communicating with the process performing the measure and
    handling user action (stopping single measure or whole process).

    Attributes
    ----------
    start_button : button
    stop_button : button
    stop_task_button : button
    show_monitor : button
    running : bool
    task_stop : bool
    process_stop : bool
    task_holders : list(instance(TaskHolder))
    process : instance(Process)
    log_thread : instance(Thread)
    log_queue : multiprocessing queue
    monitor_queue :  multiprocessing queue
    current_monitor : instance(MeasureMonitor)
    pipe : multiprocessing double ended pipe

    Methods
    -------
    append_task(new_task):

    """

    start_button = Button('Start')
    stop_button = Button('Stop all')
    stop_task_button = Button('Stop task')
    show_monitor = Button('Show monitor')
    running = Bool(False)
    task_stop = Instance(Event, ())
    process_stop = Instance(Event, ())

    task_holders = List(Instance(TaskHolder), [])

    process = Instance(Process)
    log_thread = Instance(Thread)
    log_queue = Instance(Queue, ())
    monitor_queue = Instance(Queue, ())
    current_monitor = Instance(MeasureMonitor)
    pipe = Any #Instance of Connection but ambiguous when the OS is not known

    traits_view = View(
                    VGroup(
                        VGroup(
                            UItem('task_holders',
                                  editor = ListInstanceEditor(style = 'custom',
                                                      addable = False),
                                  ),
                            show_border = True,
                            label = 'Enqueued tasks',
                            ),
                        HGroup(
                            UItem('start_button',
                              enabled_when = 'not running and task_holders'),
                            UItem('stop_task_button', enabled_when = 'running'),
                            UItem('stop_button', enabled_when = 'running'),
                            ),
                        UItem('show_monitor', enabled_when = 'running'),
                        ),
                    resizable = False,
                    width = 300,
                    handler = TaskExecutionControlHandler(),
                    )

    def append_task(self, new_task):
        """ff
        """
        check = new_task.check(
                    test_instr = not self.running)
        if check[0]:
            dialog = TaskHolderDialog()
            ui = dialog.edit_traits()
            if ui.result:
                if dialog.name == '':
                    dialog.name = 'Meas' + str(len(self.task_holders))
                task_holder = TaskHolder(root_task = new_task,
                                         name = dialog.name)
                if dialog.use_monitor:
                    res = task_holder.monitor.define_monitored_entries(
                                        task_holder.root_task.task_database)
                    task_holder.use_monitor = res
                else:
                    task_holder.use_monitor = False
                self.task_holders.append(task_holder)

                path = os.path.join(new_task.default_path, dialog.name + '.ini')
                with open(path, 'w') as f:
                    new_task.update_preferences_from_traits()
                    new_task.task_preferences.write(f)

                return True
            else:
                return False
        else:
           TaskCheckDisplay(check[1])
           return False

    def _start_button_changed(self):
        """
        """
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

    def _stop_button_changed(self):
        """
        """
        print 'Stopping process'
        self.process_stop.set()
        self.pipe.send('STOP')
        self.task_stop.set()
        self.process.join()
        self.log_thread.join()
        self.running = False

    def _stop_task_button_changed(self):
        """
        """
        print 'Stopping task'
        self.task_stop.set()

    def _show_monitor_changed(self):
        """
        """
        self.current_monitor.open_window()

    def _process_listerner(self):
        """
        """
        print 'Starting listener'
        while not self.process_stop.is_set():
            self.pipe.poll(None)
            mess = self.pipe.recv()
            print 'Message received'
            if mess == 'Need task':
                if self.task_holders:
                    i = 0
                    task = None
                    while i < len(self.task_holders):
                        if self.task_holders[i].status == 'EDITING':
                            i += 1
                            continue
                        else:
                            task_holder = self.task_holders[i]
                            task = task_holder.root_task
                            name = task_holder.name
                            break
                    if task is not None:
                        task_holder.is_running = True
                        task.update_preferences_from_traits()

                        if self.current_monitor:
                            self.current_monitor.stop_monitor()
                            self.current_monitor = None

                        if task_holder.use_monitor:
                            self.current_monitor = task_holder.monitor
                            self.current_monitor.status = 'Running'
                            self.current_monitor.start_monitor(
                                                        self.monitor_queue)
                            self.current_monitor.open_window()
                            self.pipe.send((name, task.task_preferences,
                                    self.current_monitor.monitored_map.keys()))
                        else:
                            self.pipe.send((name, task.task_preferences,
                                        None))
                        print 'Measurement sent'
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
                else:
                    if self.current_monitor:
                        self.current_monitor.status = 'Stopped'
                    self.process_stop.set()
                    print 'All measurements have been sent'
                    self.pipe.send(('','STOP',''))
                    self.pipe.poll(None)
                    self.pipe.close()
                    self.process.join()
                    self.log_thread.join()
                    self.running = False
                    break

            elif mess == 'Task processed':
                i = 0
                while i < len(self.task_holders):
                    if self.task_holders[i].status != 'RUNNING':
                        i += 1
                        continue
                    else:
                       del self.task_holders[i]
                       break

            else:
                self.pipe.close()
                self.process.join()
                self.log_thread.join()
                self.running = False
                break
        if self.current_monitor:
            self.current_monitor.status = 'Stopped'