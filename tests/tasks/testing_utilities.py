# -*- coding: utf-8 -*-
# =============================================================================
# module : loop_task.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import Bool, Value
from hqc_meas.tasks.api import SimpleTask


class CheckTask(SimpleTask):
    """
    """

    check_called = Bool()

    perform_called = Bool()

    perform_value = Value()

    def check(self, *args, **kwargs):

        self.check_called = True
        return True, {}

    def perform(self, value=None):

        self.perform_called = True
        self.perform_value = value
