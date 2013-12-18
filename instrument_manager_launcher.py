# -*- coding: utf-8 -*-
import enaml
from enaml.qt.qt_application import QtApplication
from hqc_meas.instruments.instrument_manager import InstrumentManager
with enaml.imports():
    from hqc_meas.instruments.instrument_manager_view\
                                        import InstrumentManagerView

app = QtApplication()
# Create a view and show it.
manager = InstrumentManager()
view = InstrumentManagerView(manager = manager)
view.show()

app.start()