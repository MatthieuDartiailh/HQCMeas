# -*- coding: utf-8 -*-
"""
"""
from atom.api import (Unicode, Str, Instance, Dict)
from configobj import ConfigObj
import os
from inspect import cleandoc

from .base_tasks import SimpleTask
from ..instruments.drivers import DRIVERS
from ..instruments.instrument_manager import matching_instr_list
from ..instruments.drivers.driver_tools import BaseInstrument, InstrIOError

class InstrumentTask(SimpleTask):
    """
    """
    profile_dict = Dict(Unicode(), Unicode()).tag(pref = True)
    selected_profile = Unicode().tag(pref = True)
    driver_list = []
    selected_driver = Str().tag(pref = True)
    driver = Instance(BaseInstrument)

    def check(self, *args, **kwargs):
        """
        """
        traceback = {}
        if self.selected_profile:
            full_path = self.profile_dict[self.selected_profile]
        else:
            traceback[self.task_path + '/' +self.task_name] = cleandoc(
                '''You must provide an instrument profile''')
            return False, traceback
        
        if not os.path.isfile(full_path):
            traceback[self.task_path + '/' +self.task_name] =\
                'Failed to get the specified instr profile'''
            return False, traceback

        if self.selected_driver in DRIVERS:
            driver_class = DRIVERS[self.selected_driver]
        else:
            traceback[self.task_path + '/' +self.task_name] =\
                'Failed to get the specified instr driver'''
            return False, traceback

        if kwargs['test_instr']:
            config = ConfigObj(full_path)
            try:
                instr = driver_class(config)
                instr.close_connection()
            except InstrIOError:
                traceback[self.task_path + '/' +self.task_name] = cleandoc(
                '''Failed to establish the connection with the selected
                    instrument''')
                return False, traceback

        return True, traceback

    def start_driver(self):
        """
        """
        instrs = self.task_database.get_value('root', 'instrs')
        if self.selected_profile in instrs:
            self.driver = instrs[self.selected_profile]
        else:
            full_path = self.build_profile_path()
            driver_class = DRIVERS[self.selected_driver]
            config = ConfigObj(full_path)
            self.driver = driver_class(config)
            instrs[self.selected_profile] = self.driver
            self.task_database.set_value('root', 'instrs', instrs)

    def stop_driver(self):
        """
        """
        self.driver.close_connection()

    def _observe_selected_driver(self, change):
        """
        """
        self.profile_dict = matching_instr_list(change['value'])
