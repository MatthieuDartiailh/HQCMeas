# -*- coding: utf-8 -*-

#Importing all known tasks
from ...tasks import SimpleTask, LoopTask, ComplexTask

#Importing the base task config
from .base_task_config import (AbstractConfigTask, IniConfigTask, PyConfigTask)

#Importing the config for the loop tasks
from loop_task_config import LoopConfigTask

#defining the special config dictionnary used by the builder to select the right
#config task class.
SPECIAL_CONFIG = {SimpleTask : PyConfigTask, LoopTask : LoopConfigTask,
                  ComplexTask : PyConfigTask}
                  
import enaml
with enaml.imports():
    from .base_views import SimpleView, IniView, NoneView
    from .loop_view import LoopView
    
CONFIG_MAP_VIEW = {type(None) : NoneView, PyConfigTask : SimpleView,
                   LoopConfigTask : LoopView, IniConfigTask : IniView}