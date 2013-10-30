# -*- coding: utf-8 -*-
from traits.etsconfig.etsconfig import ETSConfig
if ETSConfig.toolkit is '':
    ETSConfig.toolkit = "qt4"

from traits.api import (Str, HasTraits, Instance, on_trait_change, Button)
from traitsui.api import (View, UItem, Group, HGroup, VGroup, TextEditor,
                          Handler, Label, MenuBar, Menu, Action)
from pyface.qt import QtGui

from hqc_meas.instruments.instrument_manager import InstrumentManager
from hqc_meas.measurement.measurement_edition import MeasurementBuilder
from hqc_meas.measurement.measurement_execution import TaskExecutionControl
from hqc_meas.log_facility import (StreamToLogRedirector,
                                             GuiConsoleHandler)
import os, sys, logging
from logging.handlers import TimedRotatingFileHandler

logging.captureWarnings(True)

class Hack(Handler):
    """
    """
    def init(self, info):
        """
        """
        super(Hack, self).init(info)
        info.string.control.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                          QtGui.QSizePolicy.Fixed)

class MessagePanel(HasTraits):

    string = Str('')
    clean_button = Button('Clean')
    view = View(
            UItem('string', style = 'custom',
                  editor = TextEditor(multi_line = True,
                                          read_only = True),
                  height = -150,
                  ),
            UItem('clean_button'),
            handler = Hack()
            )

    @on_trait_change('clean_button')
    def _clean_process(self):
        self.string = ''

class TestHandler(Handler):
    """
    """
    def open_instr_manager(self, info):
        """
        """
        InstrumentManager().edit_traits()

class Test(HasTraits):
    editor = Instance(MeasurementBuilder)
    exe_control = Instance(TaskExecutionControl)
    panel_main_process = Instance(MessagePanel, ())
    panel_measure_process = Instance(MessagePanel, ())
#    button2 = Button('Print database')

    menubar = MenuBar(
                    Menu(
                        Action(name = 'Open manager',
                                action = 'open_instr_manager',
                                ),
                        name = 'Instr'),
                    )

    view = View(
                VGroup(
                    HGroup(
                        UItem('editor@'),
                        UItem('exe_control@', width = -300),
                        ),
                    Group(
                        Label('    Main process'), Label('   Measure process'),
                        UItem('panel_main_process@'),
                        UItem('panel_measure_process@'),
                        columns = 2
                        ),
#                    UItem('button2'),
                ),
                resizable = True,
                menubar = menubar,
                handler = TestHandler(),
                title = 'HQC Measurement',
                )

    def __init__(self, *args, **kwargs):
        super(Test, self).__init__(*args, **kwargs)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        gui_logger = GuiConsoleHandler({'MainProcess' : self.panel_main_process,
                                        'MeasureProcess' :
                                            self.panel_measure_process})

        if not os.path.isdir('log_files'):
            os.mkdir('log_files')
        log_path = 'log_files/measure.log'
        file_logger = TimedRotatingFileHandler(log_path, when = 'midnight')

        aux = '%(asctime)s | %(processName)s | %(levelname)s | %(message)s'
        formatter = logging.Formatter(aux)
        file_logger.setFormatter(formatter)
        logger.addHandler(file_logger)
        logger.addHandler(gui_logger)

        redir_stdout = StreamToLogRedirector(logger)
        redir_stderr = StreamToLogRedirector(logger, stream_type = 'stderr')
        sys.stdout = redir_stdout
        sys.stderr = redir_stderr

    @on_trait_change('editor:enqueue_button')
    def enqueue_measurement(self):
        self.exe_control.append_task(self.editor.root_task)

#    def _button2_changed(self):
#        pprint.pprint(self.editor.root_task.task_database._database)

if __name__ == '__main__':
    editor = MeasurementBuilder()
    editor.new_root_task()

    Test(editor = editor, exe_control = TaskExecutionControl()).configure_traits()
