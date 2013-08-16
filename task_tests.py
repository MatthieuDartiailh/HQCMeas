# -*- coding: utf-8 -*-

from traits.api import (Str, HasTraits, Instance, Button)
from traitsui.api import View, UItem, InstanceEditor, Group
from measurement.task_management.tasks import RootTask
from measurement.task_management.task_builder import TaskBuilder
from measurement.measurement_editor import MeasurementEditor
from pprint import pprint

class Test(HasTraits):
    root = Instance(RootTask)
    editor = Instance(MeasurementEditor)
    button = Button('Start')
    button2 = Button('Print database')

    view = View(UItem('editor',
                      style = 'custom',
                      ),
                UItem('button'),
                UItem('button2'),
                resizable = True,
                )

    def _button_changed(self):
        self.root.process()

    def _button2_changed(self):
        pprint(self.root.task_database._database)

root = RootTask(task_builder = TaskBuilder)
editor = MeasurementEditor(root_task = root)

Test(root = root, editor = editor).configure_traits()