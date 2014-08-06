# -*- coding: utf-8 -*-
# =============================================================================
# module : testing_utilities.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import Bool, Value, Int, Float
from hqc_meas.tasks.api import SimpleTask
from time import sleep


class CheckTask(SimpleTask):
    """
    """

    check_called = Bool()

    perform_called = Int()

    perform_value = Value()

    time = Float(0.01)

    def check(self, *args, **kwargs):

        self.check_called = True
        return True, {}

    def perform(self, value=None):

        self.perform_called += 1
        self.perform_value = value
        # Simply allow thread switching
        sleep(self.time)


class ExceptionTask(SimpleTask):

    def perform(self):
        raise Exception()


def join_threads(root):
    for pool_name in root.threads:
        with root.threads.safe_access(pool_name) as pool:
            for thread in pool:
                try:
                    thread.join()
                except Exception:
                    pass
