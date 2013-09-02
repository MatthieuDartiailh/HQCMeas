# -*- coding: utf-8 -*-
"""
"""
from traits.api import (Str, List, Instance, Dict)
from visa import Instrument
from configobj import ConfigObj
import os

from .base_tasks import SimpleTask
from ...instruments.drivers import drivers
from ...instruments.profiles import profiles_folder_path

class InstrumentTask(SimpleTask):
    """
    """
    profile_dict = Dict(Str, Str, preference = True)
    profile_list = List(Str)
    selected_profile = Str(preference = True)
    driver_list = []
    selected_driver = Str(preference = True)
    driver = Instance(Instrument)

    def check(self, *args, **kwargs):
        """
        """
        try:
            full_path = os.path.join(profiles_folder_path,
                                    self.selected_profile + '.ini')
        except:
            print 'Failed to get the specified instr profile in {}'.format(
                                                                self.task_name)
            return False
        try:
            driver_class = drivers[self.selected_driver]
        except:
            print 'Failed to get the specified instr driver in {}'.format(
                                                                self.task_name)
            return False
        if kwargs['test_instr']:
            try:
                config = ConfigObj(full_path)
                connection_str = config['connection_type']\
                                 + '::' + config['address']\
                                 + '::' + config['additionnal_mode']
                driver_class(connection_str)
            except:
                print 'Failed to establish the connection\
                    with the selected instrument in {}'.format(self.task_name)
                return False
        return True

    def start_driver(self):
        """
        """
        profile = self.profile_dict[self.selected_profile]
        full_path = os.path.join(profiles_folder_path, profile)
        driver_class = drivers[self.selected_driver]
        config = ConfigObj(full_path)
        connection_str = config['connection_type'] + '::' + config['address']\
                            + '::' + config['additionnal_mode']
        self.driver = driver_class(connection_str)
        instrs = self.task_database.get_value('root', 'instrs')
        instrs.append(self.driver)
        self.task_database.set_value('root', 'instrs', instrs)

    def stop_driver(self):
        """
        """
        self.driver.close()

    def _profile_dict_changed(self):
        """
        """
        self.profile_list = self.profile_dict.keys()
