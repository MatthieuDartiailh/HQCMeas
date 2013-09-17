# -*- coding: utf-8 -*-
"""
"""
import sys, os, logging
from logging.handlers import RotatingFileHandler
from multiprocessing import Process, Pipe, Queue
from multiprocessing.synchronize import Event
from threading import Thread
from traits.api import (HasTraits, Instance, Button, Bool, Str, Any,
                        List)
from traitsui.api import (View, UItem, HGroup, VGroup, Handler,
                        ListInstanceEditor)
from .task_management.tasks import RootTask
from .measurement_edition import MeasurementEditor
from .task_management.config import IniConfigTask
from .log.log_facility import (StreamToLogRedirector, QueueHandler,
                                   QueueLoggerThread)

class TaskProcess(Process):
    """
    """

    def __init__(self, pipe, queue, task_stop, process_stop):
        super(TaskProcess, self).__init__(name = 'MeasureProcess')
        self.task_stop = task_stop
        self.process_stop = process_stop
        self.pipe = pipe
        self.queue = queue
        self.meas_log_handler = None

    def run(self):
        """
        """
        self._config_log()
        logger = logging.getLogger()
        redir_stdout = StreamToLogRedirector(logger)
        redir_stderr = StreamToLogRedirector(logger, stream_type = 'stderr')
        sys.stdout = redir_stdout
        sys.stderr = redir_stderr
        logger.info('Logger parametrised')
        print 'Process running'
        while not self.process_stop.is_set():
            print 'Need task'
            self.pipe.send('Need task')
            self.pipe.poll(None)
            name, config = self.pipe.recv()
            if config != 'STOP':
                task = IniConfigTask().build_task_from_config(config)
                print 'Task built'
                if self.meas_log_handler != None:
                    logger.removeHandler(self.meas_log_handler)
                log_path = os.path.join(task.get_from_database('default_path'),
                                        name + '.log')
                self.meas_log_handler = RotatingFileHandler(log_path,
                                                            mode = 'w',
                                                            maxBytes = 10**6,
                                                            backupCount = 10)
                self.task_stop.clear()
                task.should_stop = self.task_stop
                task.task_database.prepare_for_running()
                if task.check(test_instr = True):
                    print 'Check successful'
                    task.process()
                    print 'Task processed'

        self.pipe.send('Closing')
        print 'Process shuting down'
        self.pipe.close()

    def _config_log(self):
        """
        """
        config_worker = {
            'version': 1,
            'disable_existing_loggers': True,
            'handlers': {
                'queue': {
                    'class': QueueHandler,
                    'queue': self.queue,
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


class TaskHolderHandler(Handler):
    """
    """
    def object_edit_button_changed(self, info):
        """
        """
        model = info.object
        meas_editor = MeasurementEditor(root_task = model.root_task,
                                        is_new_meas = False)
        model.status = 'EDITING'
        meas_editor.edit_traits(parent = info.ui.control,
                                kind = 'live',
                                )
        model.status = ''


class TaskHolder(HasTraits):
    """
    """
    name = Str
    status = Str('READY')
    edit_button = Button('Edit')
    is_running = Bool(False)
    root_task = Instance(RootTask)

    traits_view = View(
                    VGroup(
                        UItem('name', style = 'readonly'),
                        VGroup(
                            UItem('status', style = 'readonly',
                                  resizable = True),
                            show_border = True,
                            label = 'Status',
                            ),
                        UItem('edit_button', enabled_when = 'not is_running'),
                        show_border = True,
                        label = 'Task',
                        ),
                    handler = TaskHolderHandler(),
                    resizable = False,
                    height = -50,
                    )

class TaskHolderDialog(HasTraits):
    """
    """
    name = Str

    traits_view = View(UItem('name'), buttons = ['OK'],
                       title = 'Enter a name for your measurement')

class TaskExecutionControl(HasTraits):
    """
    """

    start_button = Button('Start')
    stop_button = Button('Stop all')
    stop_task_button = Button('Stop task')
    running = Bool(False)
    task_stop = Instance(Event, ())
    process_stop = Instance(Event, ())

    task_holders = List(Instance(TaskHolder), [])

    process = Instance(Process)
    thread = Instance(Thread)
    queue = Instance(Queue, ())
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
                        ),
                    resizable = False,
                    width = 300,
                    )

    def append_task(self, new_task):
        """
        """
        dialog = TaskHolderDialog().edit_traits()
        if dialog.name == '':
            dialog.name = 'Meas' + str(len(self.task_holders))
        task_holder = TaskHolder(root_task = new_task, name = dialog.name)
        self.task_holders.append(task_holder)

    def _start_button_changed(self):
        """
        """
        print 'Starting process'
        self.task_stop.clear()
        self.process_stop.clear()
        self.pipe, process_pipe = Pipe()
        self.process = TaskProcess(process_pipe,
                                   self.queue,
                                   self.task_stop,
                                   self.process_stop)
        self.thread = QueueLoggerThread(self.process, self.queue)
        self.process.start()
        self.thread.start()
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
        self.thread.join()
        self.running = False

    def _stop_task_button_changed(self):
        """
        """
        print 'Stopping task'
        self.task_stop.set()

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
                    while i < len(self.task_holders):
                        if self.task_holders[i].status == 'EDITING':
                            i += 1
                            continue
                        else:
                            task_holder = self.task_holders.pop(i)
                            task = task_holder.root_task
                            name = task_holder.name
                            break
                    if task is not None:
                        task.update_preferences_from_traits()
                        self.pipe.send((name, task.task_preferences))
                    else:
                        self.process_stop.set()
                        print 'The only task is the queue is being edited'
                        self.pipe.send(('', 'STOP'))
                        self.process.join()
                        self.thread.join()
                        self.running = False
                else:
                    self.process_stop.set()
                    print 'All tasks have been sent'
                    self.pipe.send('STOP')
                    self.process.join()
                    self.thread.join()
                    self.running = False
            else:
                self.pipe.close()
                break