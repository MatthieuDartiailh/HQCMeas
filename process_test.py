# -*- coding: utf-8 -*-

from multiprocessing import Process, Pipe
from multiprocessing.synchronize import Event
from threading import Thread
from traits.api import (HasTraits, Float, Instance, Button, Bool, Str, Any,
                        List, Int)
from traitsui.api import View, UItem, HGroup, VGroup
from time import sleep
import sys

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
                if string.endswith('\n'):
                    string = string[:-1]
                print string


class Dummy(HasTraits):

    aux = Float(1.0)
    go_on = Instance(Event)

    def process(self):
        print 'Starting dummy'
        for i in xrange(10):
            if self.go_on.is_set():
                break
            print self.aux
            sleep(0.3)

class DummyProcess(Process):

    def __init__(self, pipe, go_on, go_on_process, comm_pipe_in):
        super(DummyProcess, self).__init__()
        self.go_on = go_on
        self.go_on_process = go_on_process
        self.pipe = pipe
        self.comm_pipe_in = comm_pipe_in

    def run(self):
        redir = Text2PipeRedirector(self.comm_pipe_in)
        sys.stdout = redir
        while not self.go_on_process.is_set():
            print 'Need task'
            self.pipe.send('Need task')
            self.pipe.poll(None)
            task = self.pipe.recv()
            if task != 'STOP':
                self.go_on.clear()
                task.go_on = self.go_on
                task.process()

        self.pipe.send('Closing')
        print 'Process shuting down'
        self.pipe.close()

class StdoutRedirection(HasTraits):

    string = Str('')
    out = Any

    def write(self, mess):
        self.string += '\n' + mess

        if self.out:
            self.out.write(mess)


class Control(HasTraits):

    start = Button('Start')
    stop = Button('Stop all')
    stop_task = Button('Stop task')
    running = Bool(False)
    go_on = Instance(Event, ())
    go_on_process = Instance(Event, ())

    tasks = List(Instance(Dummy))
    counter = Int(0)
    add = Button('Add task')

    out = Instance(StdoutRedirection)
    process = Instance(Process)
    pipe = Any

    traits_view = View(
                    VGroup(
                        HGroup(
                            UItem('counter'),
                            UItem('add'),
                            ),
                        HGroup(
                            UItem('start', enabled_when = 'not running'),
                            UItem('stop_task', enabled_when = 'running'),
                            UItem('stop', enabled_when = 'running'),
                            ),
                        HGroup(
                            UItem('object.out.string', style = 'readonly'),
                            show_border = True,
                            ),
                        ),
                    resizable = True,
                    )

    def __init__(self):
        super(Control, self).__init__()
        self.out = StdoutRedirection(out = sys.stdout)
        sys.stdout = self.out

    def _start_changed(self):
        print 'Starting process'
        self.go_on.clear()
        self.go_on_process.clear()
        self.pipe, process_pipe = Pipe()
        outlet_pipe, inlet_pipe = Pipe(duplex = False)
        self.process = DummyProcess(process_pipe,
                                    self.go_on,
                                    self.go_on_process,
                                    inlet_pipe)
        self.thread = Pipe2TextThread(self.process, outlet_pipe)
        self.process.start()
        self.thread.start()
        self.running = True
        Thread(group=None, target=self._process_listerner).start()

    def _stop_changed(self):
        print 'Stopping process'
        self.go_on_process.set()
        self.pipe.send('STOP')
        self.go_on.set()
        self.process.join()
        self.running = False

    def _stop_task_changed(self):
        print 'Stopping task'
        self.go_on.set()

    def _add_changed(self):
        self.tasks.append(Dummy(aux = self.counter))#, go_on = self.go_on))
        self.counter += 1

    def _process_listerner(self):
        while not self.go_on_process.is_set():
            self.pipe.poll(None)
            mess = self.pipe.recv()
            if mess == 'Need task':
                if self.tasks:
                    task = self.tasks.pop(0)
                    self.pipe.send(task)
                    self.counter -= 1
                else:
                    self.go_on_process.set()
                    print 'Tasks all sent'
                    self.pipe.send('STOP')
                    self.process.join()
                    self.running = False
            else:
                self.pipe.close()
                break


if __name__ == '__main__':
    Control().configure_traits()
