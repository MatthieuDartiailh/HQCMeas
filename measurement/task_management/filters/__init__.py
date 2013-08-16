# -*- coding: utf-8 -*-

from base_task_filters import (AllTaskFilter, PyTaskFilter, TemplateTaskFilter,
                               SimpleTaskFilter, AbstractTaskFilter,
                               LoopableTaskFilter)

task_filters = {'All' : AllTaskFilter,
                'Python' : PyTaskFilter,
                'Template' : TemplateTaskFilter,
                'Simple' : SimpleTaskFilter,
                'Loopable' : LoopableTaskFilter}