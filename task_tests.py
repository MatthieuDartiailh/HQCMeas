# -*- coding: utf-8 -*-
from traits.etsconfig.etsconfig import ETSConfig
if ETSConfig.toolkit is '':
    ETSConfig.toolkit = "qt4"

from traits.api import (Str, HasTraits, Instance, Any,
                        on_trait_change)
from traitsui.api import (View, UItem, Group, HGroup, VGroup, TextEditor,
                          Handler, Label)
from pyface.qt import QtGui

from measurement.measurement_editor import MeasurementEditor
from measurement.measurement_execution import TaskExecutionControl
import sys

class Hack(Handler):
    """
    """
    def init(self, info):
        """
        """
        super(Hack, self).init(info)
        info.main_out.control.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                          QtGui.QSizePolicy.Fixed)
        info.process_out.control.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                          QtGui.QSizePolicy.Fixed)

class StdoutRedirection(HasTraits):

    main_out = Str('')
    process_out = Str('')
    out = Any
    view = View(
            Group(
                Label('   Main process'), Label('   Measurement process'),
                UItem('main_out', style = 'custom',
                      editor = TextEditor(multi_line = True,
                                              read_only = True),
                      height = -150,
                      ),
                UItem('process_out', style = 'custom',
                      editor = TextEditor(multi_line = True,
                                              read_only = True),
                      height = -150,
                      ),
                columns = 2,
                ),
            handler = Hack()
            )

    def write(self, mess):
        mess.strip()
        if 'Subprocess' in mess:
            self.process_out += mess.split(':')[1].strip()
        else:
            self.main_out += mess

        if self.out:
            self.out.write(mess)

class Test(HasTraits):
    editor = Instance(MeasurementEditor)
    exe_control = Instance(TaskExecutionControl)
    out = Instance(StdoutRedirection)
#    button2 = Button('Print database')

    view = View(
                VGroup(
                    HGroup(
                        UItem('editor@'),
                        UItem('exe_control@', width = -300),
                        ),
#                    UItem('button2'),
                    UItem('out@', height = -150),
                ),
                resizable = True,
                )

    def __init__(self, *args, **kwargs):
        super(Test, self).__init__(*args, **kwargs)
        self.out = StdoutRedirection(out = sys.stdout)
        sys.stdout = self.out

    @on_trait_change('editor:enqueue_button')
    def enqueue_measurement(self):
        if self.editor.root_task.check(test_instr = not self.exe_control.running):
            self.exe_control.append_task(self.editor.root_task)
            self.editor.new_root_task()

#    def _button2_changed(self):
#        pprint(self.editor.root_task.task_database._database)

if __name__ == '__main__':
    editor = MeasurementEditor()
    editor.new_root_task()

    Test(editor = editor, exe_control = TaskExecutionControl()).configure_traits()
