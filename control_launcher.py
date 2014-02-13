# -*- coding: utf-8 -*-
import enaml
from enaml.qt.qt_application import QtApplication
from hqc_meas.control.main_panel import MainPanelModel
with enaml.imports():
    from hqc_meas.control.main_view import MainPanelView

app = QtApplication()
# Create a view and show it.
manager = MainPanelModel()
view = MainPanelView(model=manager)
view.show()

app.start()
