# -*- coding: utf-8 -*-
"""
This module simply import all the tasks defined in the directory tasks and
defines one module variable KNOWN_PY_TASKS storing all the tasks succeptible
to be used as is by the user (no absract class)
"""
from .base_tasks import (AbstractTask, SimpleTask, ComplexTask, RootTask)
from .loop_tasks import (LoopTask, SimpleLoopTask, BaseLoopTask)

from .test_tasks import (PrintTask, SleepTask, DefinitionTask)
from .save_tasks import SaveTask
from .formula_task import FormulaTask
from .instr_task import InstrumentTask
from .set_dc_voltage_task import SetDcVoltageTask
from .meas_dc_voltage_task import MeasDcVoltageTask
from .lock_in_measure_task import LockInMeasureTask
from .rf_source_tasks import (RFSourceSetFrequencyTask, RFSourceSetPowerTask,
                              RFSourceSetOnOffTask)
from .pna_tasks import (PNASinglePointMeasureTask, PNAFreqSweepTask,
                        PNASetFreqTask, PNASetPowerTask)
from apply_mag_field_task import ApplyMagFieldTask

KNOWN_PY_TASKS = [ComplexTask, SimpleLoopTask, LoopTask, PrintTask, SaveTask,
                  FormulaTask, SetDcVoltageTask, MeasDcVoltageTask,
                  LockInMeasureTask, RFSourceSetFrequencyTask,
                  RFSourceSetPowerTask, RFSourceSetOnOffTask, SleepTask,
                  PNASinglePointMeasureTask, PNAFreqSweepTask,
                  PNASetFreqTask,  PNASetPowerTask,ApplyMagFieldTask,
                  DefinitionTask]