# -*- coding: utf-8 -*-
# =============================================================================
# module : instr_task.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import (Str, Instance)
from inspect import cleandoc

from hqc_meas.instruments.drivers.driver_tools import (BaseInstrument,
                                                       InstrIOError)
from .base_tasks import SimpleTask
from .task_interface import TaskInterface


class InstrumentTask(SimpleTask):
    """ Base class for all tasks calling instruments.

    """
    #: Name of the profile to use.
    selected_profile = Str().tag(pref=True)

    #: List of acceptable drivers. (class attribute)
    driver_list = []

    #: Name of the selected driver.
    selected_driver = Str().tag(pref=True)

    #: Instance of instrument driver.
    driver = Instance(BaseInstrument)

    def check(self, *args, **kwargs):
        """
        """
        run_time = self.root_task.run_time
        traceback = {}
        config = None

        if self.selected_profile:
            if 'profiles' in run_time:
                # Here use get to avoid errors if we were not granted the use
                # of the profile. In that case config won't be used.
                config = run_time['profiles'].get(self.selected_profile)
        else:
            traceback[self.task_path + '/' + self.task_name] =\
                'You must provide an instrument profile'
            return False, traceback

        if run_time and self.selected_driver in run_time['drivers']:
            driver_class = run_time['drivers'][self.selected_driver]
        else:
            traceback[self.task_path + '/' + self.task_name] =\
                'Failed to get the specified instr driver'''
            return False, traceback

        if kwargs.get('test_instr') and config:
            try:
                instr = driver_class(config)
                instr.close_connection()
            except InstrIOError:
                traceback[self.task_path + '/' + self.task_name] =\
                    cleandoc('''Failed to establish the connection with the
                              selected instrument''')
                return False, traceback

        return True, traceback

    def start_driver(self):
        """ Create an instance of the instrument driver and connect it.

        """
        run_time = self.root_task.run_time
        instrs = self.task_database.get_value('root', 'instrs')
        if self.selected_profile in instrs:
            self.driver = instrs[self.selected_profile]
        else:
            config = run_time['profiles'][self.selected_profile]
            driver_class = run_time['drivers'][self.selected_driver]
            self.driver = driver_class(config)
            instrs[self.selected_profile] = self.driver
            self.task_database.set_value('root', 'instrs', instrs)

    def stop_driver(self):
        """ Stop the instrument driver.

        """
        self.driver.close_connection()


class InstrTaskInterface(TaskInterface):
    """

    """
    #: List of acceptable drivers. (class attribute)
    driver_list = []


TASK_PACKAGES = ['tasks_instr']
