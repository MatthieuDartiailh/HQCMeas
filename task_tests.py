# -*- coding: utf-8 -*-

from traits.api import (Str, HasTraits, Instance, Button)
from traitsui.api import View, UItem, InstanceEditor, Group
from tasks.tasks import SimpleTask, ComplexTask, RootTask, LoopTask
from tasks.dummy import Measurement
from pprint import pprint

print __package__

class PrintTask(SimpleTask):

    task_name = 'Printer'
    loopable = True
    task_database_entries = ['message']
    message = Str('')

    def __init__(self, *args, **kwargs):
        super(PrintTask, self).__init__(*args, **kwargs)

        task_view = View(Group(UItem('task_name', style = 'readonly'),
                               UItem('message')))
        self.trait_view('task_view', task_view)

    def process(self, *args, **kwargs):
        self.task_database.set_value(self.task_path, 'message', self.message)
        print self.message

class TaskBuilder(object):

    def build(self, parent, ui):
        print ui
        return PrintTask(message = 'Hello World',
                         task_database = parent.task_database,
                         root_task = parent.root_task)

class FalseEditor(Measurement):

    task_builder = TaskBuilder()

class Test(HasTraits):
    root = Instance(RootTask)
    button = Button('Start')
    button2 = Button('Print database')

    view = View(UItem('root',
                      style = 'custom',
                      editor = InstanceEditor(view = 'task_view')),
                UItem('button'),
                UItem('button2'),
                resizable = True,
                )

    def _button_changed(self):
        self.root.process()

    def _button2_changed(self):
        pprint(self.root.task_database._database)

root = RootTask(task_builder = TaskBuilder)
print SimpleTask.loopable
comptask = ComplexTask(task_name = 'comp')
comptask2 = ComplexTask(task_name = 'comp2')
#looptask = LoopTask(task_name = 'loop', task = PrintTask)
root.children_task = [PrintTask(message = 'READY', task_name = 'Printer 1'),
                      comptask, comptask2]
toto = PrintTask(message = 'EXIT', task_name = 'Printer 3')
toto.task_name = 'toto'
comptask.children_task = [PrintTask(message = 'GO',task_name = 'Printer 2'),toto]

Test(root = root).configure_traits()