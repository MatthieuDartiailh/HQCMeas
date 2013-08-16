# -*- coding: utf-8 -*-
from traits.api import Str
from traitsui.api import (View, Group, UItem, Label, HGroup)
from .base_tasks import SimpleTask

class PrintTask(SimpleTask):
    """Basic task which simply prints a message in stdout. Loopable.
    """

    loopable = True
    task_database_entries = ['message']
    message = Str('', preference = True)
    task_view = View(
                    Group(
                        UItem('task_name', style = 'readonly'),
                        HGroup(
                            Label('Message'),
                            UItem('message'),
                            ),
                        ),
                    )

    def process(self, *args, **kwargs):
        self.write_in_database('message', self.message)
        print self.message