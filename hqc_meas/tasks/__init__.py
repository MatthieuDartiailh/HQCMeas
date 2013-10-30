# -*- coding: utf-8 -*-
"""
This module simply import all the tasks defined in the directory tasks and
defines one module variable KNOWN_PY_TASKS storing all the tasks succeptible
to be used as is by the user (no absract class)
"""
from .base_tasks import (AbstractTask, SimpleTask, ComplexTask, RootTask)
from .loop_tasks import (LoopTask, SimpleLoopTask, BaseLoopTask)

from .test_tasks import (PrintTask, SleepTask, DefinitionTask)
from .save_tasks import (SaveTask, SaveArrayTask)
from .formula_task import FormulaTask
from .instr_task import InstrumentTask
from .set_dc_voltage_task import SetDCVoltageTask
from .meas_dc_voltage_task import MeasDCVoltageTask
from .lock_in_measure_task import LockInMeasureTask
from .rf_source_tasks import (RFSourceSetFrequencyTask, RFSourceSetPowerTask,
                              RFSourceSetOnOffTask)
from .pna_tasks import (PNASinglePointMeasureTask, PNASweepTask,
                        PNASetFreqTask, PNASetPowerTask)
from .apply_mag_field_task import ApplyMagFieldTask
from .array_tasks import ArrayExtremaTask

KNOWN_PY_TASKS = [ComplexTask, SimpleLoopTask, LoopTask, PrintTask, SaveTask,
                  FormulaTask, SetDCVoltageTask, MeasDCVoltageTask,
                  LockInMeasureTask, RFSourceSetFrequencyTask,
                  RFSourceSetPowerTask, RFSourceSetOnOffTask, SleepTask,
                  PNASinglePointMeasureTask, PNASweepTask,
                  PNASetFreqTask,  PNASetPowerTask,ApplyMagFieldTask,
                  DefinitionTask, SaveArrayTask, ArrayExtremaTask]