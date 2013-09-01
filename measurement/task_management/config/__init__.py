# -*- coding: utf-8 -*-

#Importing all known tasks
from ..tasks import *

#Importing the base task config
from .base_task_config import (AbstractConfigTask, IniConfigTask, PyConfigTask,
                              ComplexTask)
from .instr_task_config import (InstrConfigTask)

#Importing all the config for the simple task, potentially loopable


#Importing the config for the loop tasks
from loop_task_config import LoopConfigTask

#defining the special config dictionnary used by the builder to select the right
#config task class.
special_config = {SimpleTask : PyConfigTask, InstrumentTask : InstrConfigTask,
                  LoopTask : LoopConfigTask, ComplexTask : PyConfigTask}