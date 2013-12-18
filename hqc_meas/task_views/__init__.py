# -*- coding: utf-8 -*-

from ..tasks import *

import enaml
with enaml.imports():
    from base_task_view import ComplexView, RootView, NoneView
    from test_tasks_view import PrintView, SleepView, DefinitionView
    from loop_task_views import SimpleLoopView, LoopView
    from formula_view import FormulaView
    from array_views import ArrayExtremaView
    from apply_mag_field_view import ApplyMagFieldView
    from lock_in_meas_view import LockInMeasView
    from meas_dc_views import DCVoltMeasView
    from pna_task_views import (PNASetFreqView, PNASetPowerView, 
                                PNASinglePointView, PNASweepMeasView)
    from rf_source_views import (RFSourceFrequencyView, RFSourcePowerView,
                                 RFSourceSetOnOffView)
    from save_views import SaveView, SaveArrayView
    from set_dc_voltage_view import SetDcVoltageView
    
    
TASK_VIEW_MAPPING = {type(None) : NoneView,
                     RootTask : RootView,
                     ComplexTask : ComplexView,
                     PrintTask : PrintView,
                     SleepTask : SleepView,
                     DefinitionTask : DefinitionView,
                     SimpleLoopTask : SimpleLoopView,
                     LoopTask : LoopView,
                     FormulaTask : FormulaView,
                     ArrayExtremaTask : ArrayExtremaView,
                     ApplyMagFieldTask : ApplyMagFieldView,
                     LockInMeasureTask : LockInMeasView,
                     MeasDCVoltageTask : DCVoltMeasView,
                     PNASetFreqTask : PNASetFreqView,
                     PNASetPowerTask : PNASetPowerView,
                     PNASinglePointMeasureTask : PNASinglePointView,
                     PNASweepTask : PNASweepMeasView,
                     RFSourceSetFrequencyTask : RFSourceFrequencyView,
                     RFSourceSetPowerTask : RFSourcePowerView,
                     RFSourceSetOnOffTask : RFSourceSetOnOffView,
                     SaveTask : SaveView,
                     SaveArrayTask : SaveArrayView,
                     SetDCVoltageTask : SetDcVoltageView}