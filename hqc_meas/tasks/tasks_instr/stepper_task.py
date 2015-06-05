# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 16:38:18 2015

@author: lcontamin
"""

from atom.api import (Enum, Int, Range, Unicode, set_default)

from hqc_meas.tasks.api import InstrumentTask
from inspect import cleandoc


def check_channel(driver, channel):
    if driver and not channel in driver.anm150.available:
        return cleandoc('''Channel {} is not available in the 
                           controller'''.format(channel))

        
class SetSteppingParametersTask(InstrumentTask):
    """Set the amplitude and frequency of an ANM module embedded in an ANC
    controller.
    
    """
    # Axis/Channel on which to set the parameters
    # check if high is inclusive or not
    channel = Range(low=1, high=8).tag(pref=True)  
    
    # Amplitude of the steps
    amplitude = Unicode().tag(pref=True, feval=True)

    # Frequency of the steps
    frequency = Unicode().tag(pref=True, feval=True)

    driver_list = ['ANC300']
    loopable = False
    task_database_entries = set_default({'frequency': 1000, 'voltage': 15})

    def perform(self):
        """
        """
        if not self.driver:
            self.initialize()
        if self.driver.owner != self.task_name or not self.driver.connected:
            self.driver.owner = self.task_name

        channel = self.driver.anm150[self.channel]
        # check redundant with tag feval 
        channel.amplitude = self.format_and_eval_string(self.amplitude)
        channel.frequency = self.format_and_eval_string(self.frequency)
        for val, name in [(self.amplitude, 'voltage'),
                          (self.frequency, 'frequency')]:
                self.write_in_database(name, self.format_and_eval_string(val))
        # two evaluations of val but the above lines will be supressed

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(SetSteppingParametersTask, self).check(*args, 
                                                                    **kwargs)                                                          
        # redundant with tag feval 
        for val, name, symb in [(self.amplitude, 'voltage', '-volt'),
                                (self.frequency, 'frequency', '-freq')]:
            if not val:
                continue
            try:
                evaluated = self.format_and_eval_string(val)
                self.write_in_database(name, evaluated)
            except Exception as e:
                test = False
                traceback[self.task_path + '/' + self.task_name + symb] = \
                    cleandoc('''Failed to eval the {} value formula
                             {} : {}'''.format(name, val, e))

        mess = check_channel(self.driver, self.channel)
        if mess:
            test = False
            traceback[self.task_path + '/' + self.task_name + '_channel'] = \
                mess

        return test, traceback


class SteppingTask(InstrumentTask):

    # Axis/Channel on which to set the parameters
    channel = Range(low=1, high=7).tag(pref=True)  

    # Direction of stepping
    direction = Enum('Up', 'Down').tag(pref=True)

    # Number of steps
    steps = Int(low=1).tag(pref=True)

    driver_list = ['ANC300']
    loopable = False
    parallel = set_default({'activated': True, 'pool': 'instr'})
    task_database_entries = set_default({'frequency': 1000, 'voltage': 15})

    def perform(self):
        """
        """
        if not self.driver:
            self.initialize()
        if self.driver.owner != self.task_name or not self.driver.connected:
            self.driver.owner = self.task_name
            
        self.driver.step(self.direction, self.steps)

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(SetSteppingParametersTask, self).check(*args, 
                                                                    **kwargs)                                                          
        mess = check_channel(self.driver, self.channel)
        if mess:
            test = False
            traceback[self.task_path + '/' + self.task_name + '_channel'] = \
                mess

        return test, traceback

KNOWN_PY_TASKS = [SetSteppingParametersTask, SteppingTask]