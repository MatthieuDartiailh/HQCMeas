# -*- coding: utf-8 -*-
"""
"""
from traits.api import (List, Str)
from traitsui.api import (View, UItem, TextEditor, HGroup, Label, EnumEditor)

from .base_task_config import PyConfigTask
from ...instruments.drivers import drivers
from ...instruments.instrument_manager import InstrumentManager

DRIVER_LIST = drivers.keys()

class InstrConfigTask(PyConfigTask):
    """
    """
    drivers = List(Str)
    driver = Str
    config_view = View(
                    HGroup(
                        Label('Task name'),
                        UItem('task_name'),
                        ),
                    HGroup(
                        Label('Select driver'),
                        UItem('driver',
                              editor = EnumEditor(name = 'drivers')
                              ),
                        ),
                    UItem('task_doc', style = 'readonly',
                          editor = TextEditor(multi_line = True),
                          resizable = True),
                    )

    def __init__(self, *args, **kwargs):
        super(InstrConfigTask, self).__init__(*args, **kwargs)
        self.drivers = list(set(self.task_class.driver_list) & set(DRIVER_LIST))

    def build_task(self):
        """
        """
        manager = InstrumentManager()
        profile_dict = manager.matching_instr_list(self.driver)
        return self.task_class(task_name = self.task_name,
                               profile_dict = profile_dict,
                               selected_driver = self.driver)

    def check_parameters(self):
        if self.task_name != '' and self.driver != '':
            self.config_ready = True
        else:
            self.config_ready = False
