# -*- coding: utf-8 -*-
#==============================================================================
# module : pna_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""

"""

from traits.api import (Float, Str, Int, List)
from traitsui.api import (View, Group, VGroup, UItem, Label, EnumEditor)

import time, logging, re, os
from inspect import cleandoc
from configobj import ConfigObj
from textwrap import fill

from .instr_task import InstrumentTask
from .tools.task_decorator import (make_stoppable, smooth_instr_crash)
from ...instruments.profiles import PROFILES_DIRECTORY_PATH
from ...instruments.drivers import DRIVERS
from ...instruments.drivers.driver_tools import InstrIOError

class PNATasks(InstrumentTask):
    """
    """
    channels = List(Int)

    def check(self, *args, **kwargs):
        """
        """
        traceback = {}
        profile = self.profile_dict[self.selected_profile]
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
            except InstrIOError:
                traceback[self.task_path + '/' +self.task_name] = cleandoc(
                '''Failed to establish the connection with the selected
                    instrument''')
                return False, traceback

        channels_present = True
        for channel in self.channels:
            if channel not in instr.defined_channels:
                traceback[self.task_path + '/' +self.task_name] = cleandoc(
                '''Channel {} is not defined in the PNA {}, please define it
                yourself and try again.'''.format(channel,
                                                  self.selected_profile))
                channels_present = False

        if not channels_present:
            return False, traceback

        for i, entry in enumerate(self.task_database_entries):
            self.write_in_database(entry, self.task_database_entries_default[i])

        return True, traceback

class SinglePointMeasure(PNATasks):
    """
    """

    frequency = Str
    power = Str
    measures = List(Str)

    if_bandwidth = Int
    window = Int

    driver_list = ['AgilentPNA']
    task_database_entries = []
    task_database_entries_default = []

    def process(self):
        """
        """
        if not self.driver:
            self.start_driver