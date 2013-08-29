# -*- coding: utf-8 -*-
"""
"""
from traits.api import (Str, List, Instance)
from visa import Instrument
import os

from .base_tasks import SimpleTask
from ...instruments import drivers
from ...instruments.profiles import profiles_folder_path

class InstrumentTask(SimpleTask):
    """
    """
    profile_list = List(Str, preference = True)
    selected_profile = Str(preference = True)
    driver_name = Str(preference = True)
    driver_obj = Instance(Instrument)

    def check(self, *args, **kwargs):
        """
        """
        try:
            full_path = os.path.join(profiles_folder_path,
                                    self.selected_profile)
        except:
            print 'Failed to get the specified instr profile in \
                        {}'.format(self.task_name)
            return False
        try:
            driver = getattr(drivers, self.driver_name)
        except:
            print 'Failed to get the specified instr driver in \
                        {}'.format(self.task_name)
            return False
        if kwargs['test_instr']:
            try:
                driver(full_path)
            except:
                print 'Failed to establish the connection\
                    with the selected instrument in {}'.format(self.task_name)
                return False
        return True