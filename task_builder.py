# -*- coding: utf-8 -*-
"""
"""

from traits.api import (HasTraits, List, Str, Instance, Int, Type, Dict)

from tasks import AbstractTask
from task_config import BaseTaskConfig, special_config
from instrument_manager import InstrumentManager
from task_maanger import TaskManager

class TaskBuilder(HasTraits):
    """
    """

    task_manager = Instance(TaskManager)
    tasks = List(Str)
    selected_task_ind = Int

    task_filters_name = List(Str)
    selected_filter_ind = Int

    configurable_tasks = Dict(Type(AbstractTask),
                              Type(BaseTaskConfig),
                              special_config)

    instr_manager = Instance(InstrumentManager)
    recorded_instr = List(Str)