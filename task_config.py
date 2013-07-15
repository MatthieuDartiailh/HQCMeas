# -*- coding: utf-8 -*-
"""
"""

from traits.api import HasTraits, List, Type, Str, Instance
from traitsui.api import View, UItem, TextEditor

from tasks import AbstractTask
from instrument_manager import InstrumentManager
from task_builder import TaskBuilder

class ConfigTask(HasTraits):
    """
    """

    builder = Instance(TaskBuilder)
    instr_manager = Instance(InstrumentManager)
    task_class = Type(AbstractTask)
    task_doc = Str
    instr = List(Str)
    tasks = List(Str)
    traits_view = View(
                    UItem('task_doc', style = 'readonly',
                          editor = TextEditor(multi_line = True)
                          )
                      )


    def __init__(self, *args, **kwargs):
        super(ConfigTask, self).__init__(*args, **kwargs)
