# -*- coding: utf-8 -*-

from base_task_filters import (AllTaskFilter, PyTaskFilter, TemplateTaskFilter,
                               SimpleTaskFilter, AbstractTaskFilter,
                               LoopableTaskFilter, InstrumentTaskFilter,
                               LoopTaskFilter)

TASK_FILTERS = {'All': AllTaskFilter,
                'Python': PyTaskFilter,
                'Template': TemplateTaskFilter,
                'Simple': SimpleTaskFilter,
                'Loopable': LoopableTaskFilter,
                'Instrs': InstrumentTaskFilter,
                'Loop': LoopTaskFilter}
