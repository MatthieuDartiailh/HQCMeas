# -*- coding: utf-8 -*-
#============================================================================
# module : stepper_task.py
# author : Lauriane Contamin
# license : MIT license
#============================================================================
"""
"""
from atom.api import (Enum, Int, Range, Unicode, set_default)

from hqc_meas.tasks.api import InstrumentTask
from inspect import cleandoc
from hqc_meas.instruments.driver_tools import InstrIOError


def check_channel(driver, channel):
    if driver and not channel in driver.anm150.available:
        return cleandoc('''Channel {} is not available in the 
                           controller'''.format(channel))

class HackCheckInstrTask(InstrumentTask):
    """
    Temporary class (until migration to Lantz) that overwrites the check
    since the driver doesn't have a close_connection method (and the 
    driver starting is a bit different)
    """
    
    def check(self, *args, **kwargs):
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
                instr.initialize()
            except InstrIOError:
                traceback[self.task_path + '/' + self.task_name] =\
                    cleandoc('''Failed to establish the connection with the
                              selected instrument''')
                return False, traceback

        return True, traceback
    
class SetSteppingParametersTask(HackCheckInstrTask):
    """Set the amplitude and frequency of an ANM module embedded in an ANC
    controller.
    
    """
    #:: Axis/Channel on which to set the parameters
    # check if high is inclusive or not
    channel = Range(low=1, high=8).tag(pref=True)  
    
    #:: Amplitude of the steps
    amplitude = Unicode().tag(pref=True, feval=True)

    #:: Frequency of the steps
    frequency = Unicode().tag(pref=True, feval=True)

    driver_list = ['ANC300']
    loopable = False
    task_database_entries = set_default({'frequency': 1000, 'voltage': 15})

    def start_driver(self):
        super(SetSteppingParametersTask, self).start_driver()
        self.driver.initialize()
        
    def perform(self):
        """
        """
        if not self.driver:
            self.start_driver()
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
        run_time = self.root_task.run_time
        test, traceback = super(SetSteppingParametersTask, self).check(*args, 
                                                                    **kwargs)
                                                                  
        # check if given Str expressions are correct; redundant with tag feval 
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

        if not self.channel:
            test = False
            traceback[self.task_path + '/' + self.task_name + '-channel'] = \
                cleandoc('''No channel was selected''')

        if test and kwargs.get('test_instr'):
            config = run_time['profiles'].get(self.selected_profile)
            driver_class = run_time['drivers'][self.selected_driver]
            instr = driver_class(config)
            instr.initialize()
            
            mess = check_channel(instr, self.channel)
            instr.finalize()
            if mess:
                test = False
                traceback[self.task_path + '/' + self.task_name + \
                          '-channel'] = mess

        return test, traceback

class SteppingTask(HackCheckInstrTask):
    """ Launches stepping on a selected ANM module. One can specify the number
    of steps (negative for continuous stepping) and the direction.
    """
    #:: Axis/Channel on which to set the parameters
    channel = Range(low=1, high=8).tag(pref=True)  

    #:: Direction of stepping
    direction = Enum('Up', 'Down').tag(pref=True)

    #:: Number of steps
    steps = Int().tag(pref=True)

    driver_list = ['ANC300']
    loopable = False
    parallel = set_default({'activated': True, 'pool': 'instr'})
    task_database_entries = set_default({'frequency': 1000, 'voltage': 15})

    def start_driver(self):
        super(SteppingTask, self).start_driver()
        self.driver.initialize()
        
    def perform(self):
        """
        """
        if not self.driver:
            self.initialize()
        if self.driver.owner != self.task_name or not self.driver.connected:
            self.driver.owner = self.task_name
            
        channel = self.driver.anm150[self.channel]
        channel.step(self.direction, self.steps)

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(SteppingTask, self).check(*args, **kwargs) 
                                                       
        mess = check_channel(self.driver, self.channel)
        if mess:
            test = False
            traceback[self.task_path + '/' + self.task_name + '-channel'] = \
                mess

        return test, traceback


class StopSteppingTask(HackCheckInstrTask):
    """
    Stop any motion of the ANC controller, useful for example after a 
    continuous stepping.
    """
    
    driver_list = ['ANC300']
    loopable = False
    parallel = set_default({'activated': True, 'pool': 'instr'})

    def start_driver(self):
        super(SteppingTask, self).start_driver()
        self.driver.initialize()

    def perform(self):
        """
        """
        if not self.driver:
            self.initialize()
        if self.driver.owner != self.task_name or not self.driver.connected:
            self.driver.owner = self.task_name
            
        self.driver.stop_motion()


KNOWN_PY_TASKS = [SetSteppingParametersTask, SteppingTask, StopSteppingTask]