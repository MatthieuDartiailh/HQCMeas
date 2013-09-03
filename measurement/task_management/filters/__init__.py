# -*- coding: utf-8 -*-

from base_task_filters import (AllTaskFilter, PyTaskFilter, TemplateTaskFilter,
                               SimpleTaskFilter, AbstractTaskFilter,
                               LoopableTaskFilter, InstrumentTaskFilter)

task_filters = {'All' : AllTaskFilter,
                'Python' : PyTaskFilter,
                'Template' : TemplateTaskFilter,
                'Simple' : SimpleTaskFilter,
                'Loopable' : LoopableTaskFilter,
                'Instrs' : InstrumentTaskFilter}