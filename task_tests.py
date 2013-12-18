# -*- coding: utf-8 -*-

from atom.api import (Typed, Atom, Str)
from enaml.qt.qt_application import QtApplication
import enaml
with enaml.imports():
    from hqc_main import HqcMainWindow

from hqc_meas.measurement.measure import Measure
from hqc_meas.measurement.measurement_execution import TaskExecutionControl
from hqc_meas.log_facility import (StreamToLogRedirector,
                                             GuiConsoleHandler)
import os, sys, logging
from logging.handlers import TimedRotatingFileHandler

logging.captureWarnings(True)

class NotificationModel(Atom):
    
    string = Str()

class Main(Atom):
    
    meas = Typed(Measure, ())
    exe_control = Typed(TaskExecutionControl, ())
    main_log = Typed(NotificationModel,())
    meas_log = Typed(NotificationModel,())
#    button2 = Button('Print database')

    def __init__(self, **kwargs):
        super(Main, self).__init__(**kwargs)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        gui_logger = GuiConsoleHandler({'MainProcess' : self.main_log,
                                        'MeasureProcess' :
                                            self.meas_log})

        if not os.path.isdir('log_files'):
            os.mkdir('log_files')
        log_path = 'log_files/measure.log'
        file_logger = TimedRotatingFileHandler(log_path, when = 'midnight')

        aux = '%(asctime)s | %(processName)s | %(levelname)s | %(message)s'
        formatter = logging.Formatter(aux)
        file_logger.setFormatter(formatter)
        logger.addHandler(file_logger)
        logger.addHandler(gui_logger)

#        redir_stdout = StreamToLogRedirector(logger)
#        redir_stderr = StreamToLogRedirector(logger, stream_type = 'stderr')
#        sys.stdout = redir_stdout
#        sys.stderr = redir_stderr

    def enqueue_measurement(self):
        self.exe_control.append_meas(self.meas)

#    def _button2_changed(self):
#        pprint.pprint(self.editor.root_task.task_database._database)

if __name__ == '__main__':
    main_model = Main()
    app = QtApplication()
    view = HqcMainWindow(main_model = main_model)
    view.show()
    view.maximize()
    
    app.start()