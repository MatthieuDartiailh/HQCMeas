# -*- coding: utf-8 -*-
#==============================================================================
# module : test_set_dc_voltage.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from nose.tools import assert_equal
from multiprocessing import Event

from hqc_meas.tasks.api import RootTask
from hqc_meas.tasks.instr_task.set_dc_voltage_task\
    import (SetDCVoltageTask, SimpleVoltageSourceInterface,
            MultiChannelVoltageSourceInterface)

import enaml
with enaml.imports():
    from hqc_meas.tasks.instr_task.views.set_dc_voltage_view\
        import SetDCVoltageView

from ...util import process_app_events, close_all_windows
from .instr_helper import InstrHelper
