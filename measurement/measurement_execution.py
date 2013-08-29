# -*- coding: utf-8 -*-
"""
"""
import sys
from multiprocessing import Process, Pipe
from multiprocessing.synchronize import Event
from threading import Thread
from traits.api import (HasTraits, Instance, Button, Bool, Str, Any,
                        List)
from traitsui.api import (View, UItem, HGroup, VGroup, Handler,
                        ListInstanceEditor)
from .task_management.tasks import RootTask
from .measurement_editor import MeasurementEditor
from .task_management.config import IniConfigTask


class Text2PipeRedirector(object):
    """
    """
    def __init__(self, pipe_inlet):
        self.pipe_inlet = pipe_inlet
    def write(self, string):
        self.pipe_inlet.send(string.rstrip())
    def flush(self):
        return None

class Pipe2TextThread(Thread):
    """Worker Thread Class."""
    def __init__(self, process, pipe_outlet):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self.process = process
        self.pipe_outlet = pipe_outlet

    def run(self):
        """
        Pull any output from the pipe while the process runs
        """
        while self.process.is_alive():
            #Collect all display output from process
            while self.pipe_outlet.poll():
                string = self.pipe_outlet.recv()
                string.rstrip()
                if string != '':
                    print string.rstrip()

class TaskProcess(Process):
    """
    """

    def __init__(self, pipe, comm_pipe_in, task_stop, process_stop):
        super(TaskProcess, self).__init__()
        self.task_stop = task_stop
        self.process_stop = process_stop
        self.pipe = pipe
        self.comm_pipe_in = comm_pipe_in

    def run(self):
        """
        """
        redir = Text2PipeRedirector(self.comm_pipe_in)
        sys.stdout = redir
        print 'Process running'
#        sys.stderr = redir
        while not self.process_stop.is_set():
            print 'Need task'
            self.pipe.send('Need task')
            self.pipe.poll(None)
            config = self.pipe.recv()
            if config != 'STOP':
                task = IniConfigTask().build_task_from_config(config)
                print 'Task built'
                print task.children_task
                self.task_stop.clear()
                task.should_stop = self.task_stop
                task.task_database.prepare_for_running()
                if task.check():
                    print 'Check successful'
                    task.process()
                    print 'Task processed'

        self.pipe.send('Closing')
        print 'Process shuting down'
        self.pipe.close()

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
    status = Str('')
    edit_button = Button('Edit')
    is_running = Bool(False)
    root_task = Instance(RootTask)

    traits_view = View(
                    VGroup(
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
        task_holder = TaskHolder(root_task = new_task)
        self.task_holders.append(task_holder)

    def _start_button_changed(self):
        print 'Starting process'
        self.task_stop.clear()
        self.process_stop.clear()
        self.pipe, process_pipe = Pipe()
        outlet_pipe, inlet_pipe = Pipe(duplex = False)
        self.process = TaskProcess(process_pipe,
                                   inlet_pipe,
                                   self.task_stop,
                                   self.process_stop)
        self.thread = Pipe2TextThread(self.process, outlet_pipe)
        self.process.start()
        self.thread.start()
        self.running = True
        Thread(group = None, target = self._process_listerner).start()

    def _stop_button_changed(self):
        print 'Stopping process'
        self.process_stop.set()
        self.pipe.send('STOP')
        self.task_stop.set()
        self.process.join()
        self.thread.join()
        self.running = False

    def _stop_task_button_changed(self):
        print 'Stopping task'
        self.task_stop.set()

    def _process_listerner(self):
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
                            task = self.task_holders.pop(i).root_task
                            break
                    if task is not None:
                        task.update_preferences_from_traits()
                        self.pipe.send(task.task_preferences)
                    else:
                        self.process_stop.set()
                        print 'The only task is the queue is being edited'
                        self.pipe.send('STOP')
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