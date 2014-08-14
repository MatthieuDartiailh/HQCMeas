# -*- coding: utf-8 -*-
# =============================================================================
# module : sleep_task.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import (Float, set_default)

from time import sleep

from ..base_tasks import SimpleTask


class SleepTask(SimpleTask):
    """Simply sleeps for the specified amount of time.

    Wait for any parallel operation before execution by default.

    """
    #: Time during which to sleep.
    time = Float().tag(pref=True)

    wait = set_default({'activated': True})  # Wait on all pools by default.

    def perform(self):
        """ Sleep.

        """
        sleep(self.time)

    def check(self, *args, **kwargs):
        if self.time < 0:
            return False, {self.task_path + '/' + self.task_name:
                           'Sleep time must be positive.'}

        return True, {}

KNOWN_PY_TASKS = [SleepTask]
