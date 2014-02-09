# -*- coding: utf-8 -*-
from enaml.qt.qt_application import QtApplication

from hqc_meas.debug.driver_debugger import DriverDebugger
import enaml
with enaml.imports():
    from hqc_meas.debug.driver_debugger_view import DriverDebuggerView

app = QtApplication()
# Create a view and show it.
debugger = DriverDebugger()
view = DriverDebuggerView(model = debugger)
view.show()

app.start()
