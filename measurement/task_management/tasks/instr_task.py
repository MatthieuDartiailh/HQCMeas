# -*- coding: utf-8 -*-
"""
"""
from traits.api import (Str, List, Instance, Dict)
from configobj import ConfigObj
import os
from inspect import cleandoc

from .base_tasks import SimpleTask
from ...instruments.drivers import DRIVERS
from ...instruments.profiles import PROFILES_DIRECTORY_PATH
from ...instruments.instrument_manager import InstrumentManager
from ...instruments.drivers.driver_tools import BaseInstrument, InstrIOError

class InstrumentTask(SimpleTask):
    """
    """
    profile_dict = Dict(Str, Str, preference = True)
    profile_list = List(Str)
    selected_profile = Str(preference = True)
    driver_list = []
    selected_driver = Str(preference = True)
    driver = Instance(BaseInstrument)

    def check(self, *args, **kwargs):
        """
        """
        traceback = {}
        if self.selected_profile:
            profile = self.profile_dict[self.selected_profile]
        else:
            traceback[self.task_path + '/' +self.task_name] = cleandoc(
                '''You must provide an instrument profile''')
            return False, traceback

        full_path = os.path.join(PROFILES_DIRECTORY_PATH,
                                    profile)
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
            profile = self.profile_dict[self.selected_profile]
            full_path = os.path.join(PROFILES_DIRECTORY_PATH, profile)
            driver_class = DRIVERS[self.selected_driver]
            config = ConfigObj(full_path)
            self.driver = driver_class(config)
            instrs[self.selected_profile] = self.driver
            self.task_database.set_value('root', 'instrs', instrs)

    def stop_driver(self):
        """
        """
        self.driver.close_connection()

    def _profile_dict_changed(self):
        """
        """
        self.profile_list = self.profile_dict.keys()

    def _selected_driver_changed(self, new):
        """
        """
        manager = InstrumentManager()
        self.profile_dict = manager.matching_instr_list(new)
