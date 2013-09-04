# -*- coding: utf-8 -*-
"""
This module simply import all the tasks defined in the directory tasks and
defines one module variable KNOWN_PY_TASKS storing all the tasks succeptible
to be used as is by the user (no absract class)
"""
from .base_tasks import (AbstractTask, SimpleTask, ComplexTask,
                        LoopTask, RootTask)

from .test_tasks import (PrintTask)
from .save_task import SaveTask
from .formula_task import FormulaTask
from .instr_task import InstrumentTask
from .set_dc_voltage_task import SetDcVoltageTask
from .meas_dc_voltage_task import MeasDcVoltageTask
from .lock_in_measure_task import LockInMeasureTask

KNOWN_PY_TASKS = [ComplexTask, LoopTask, PrintTask, SaveTask, FormulaTask,
                  SetDcVoltageTask, MeasDcVoltageTask, LockInMeasureTask]