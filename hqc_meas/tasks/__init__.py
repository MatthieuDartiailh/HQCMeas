# -*- coding: utf-8 -*-
"""
This module simply import all the tasks defined in the directory tasks and
defines one module variable KNOWN_PY_TASKS storing all the tasks succeptible
to be used as is by the user (no absract class)
"""
from .base_tasks import (BaseTask, SimpleTask, ComplexTask, RootTask)
from .loop_tasks import (LoopTask, SimpleLoopTask, BaseLoopTask)
from .instr_task import (InstrumentTask)

if 'KNOWN_PY_TASKS' not in globals():
    import os.path, importlib, inspect
    KNOWN_PY_TASKS = [ComplexTask, SimpleLoopTask, LoopTask]
    dir_path = os.path.dirname(__file__)
    modules = ['.' + os.path.split(path)[1][:-3] 
                for path in os.listdir(dir_path)
                    if path.endswith('.py')]
    modules.remove('.__init__')
    modules.remove('.base_tasks')
    modules.remove('.loop_tasks')
    modules.remove('.instr_task')
    task_test = lambda obj: inspect.isclass(obj) and issubclass(obj, BaseTask)
    for module in modules:
        mod = importlib.import_module(module, __name__)
        if hasattr(mod, 'KNOWN_PY_TASKS'):
            KNOWN_PY_TASKS.extend(mod.KNOWN_PY_TASKS)
        else:
            tasks = inspect.getmembers(mod, task_test)
            KNOWN_PY_TASKS.extend([task[1] for task in tasks])