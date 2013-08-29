# -*- coding: utf-8 -*-

from base_tasks import (AbstractTask, SimpleTask, ComplexTask,
                        LoopTask, RootTask)

from test_tasks import (PrintTask)
from save_task import SaveTask
from formula_task import FormulaTask
from instr_task import InstrumentTask

known_py_tasks = [ComplexTask, LoopTask, PrintTask, SaveTask, FormulaTask]