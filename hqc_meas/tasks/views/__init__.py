# -*- coding: utf-8 -*-

import enaml
with enaml.imports():
    from .base_task_views import ComplexView, RootView, NoneView
    from .loop_task_views import SimpleLoopView, LoopView

if 'TASK_VIEW_MAPPING' not in globals():
    import os.path, importlib
    from ..base_tasks import RootTask, ComplexTask
    from ..loop_tasks import SimpleLoopTask, LoopTask

    TASK_VIEW_MAPPING = {type(None): NoneView,
                         RootTask: RootView,
                         ComplexTask: ComplexView,
                         SimpleLoopTask: SimpleLoopView,
                         LoopTask: LoopView}

    dir_path = os.path.dirname(__file__)
    modules = ['.' + os.path.split(path)[1][:-6]
               for path in os.listdir(dir_path)
               if path.endswith('.enaml')]
    modules.remove('.base_task_views')
    modules.remove('.loop_task_views')
    modules.remove('.task_editor')
    with enaml.imports():
        for module in modules:
            mod = importlib.import_module(module, __name__)
            TASK_VIEW_MAPPING.update(getattr(mod, 'TASK_VIEW_MAPPING'))
