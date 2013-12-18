# -*- coding: utf-8 -*-
"""
"""
from atom.api import (Str, Bool, set_default, Enum)

from .instr_task import InstrumentTask
from .tools.task_decorator import (smooth_instr_crash)
from .tools.database_string_formatter import format_and_eval_string

class RFSourceSetFrequencyTask(InstrumentTask):
    """Set the frequency of the signal delivered by the source.
    """

    frequency = Str().tag(pref = True)
    unit = Enum('GHz', 'MHz', 'KHz', 'Hz').tag(pref = True)
    auto_start = Bool(False).tag(pref = True)

    driver_list = ['AgilentE8257D']
    task_database_entries = set_default({'frequency' : 1.0, 'unit' : 'GHZ'})
    loopable = True

    @smooth_instr_crash
    def process(self, frequency = None):
        """
        """
        if not self.driver:
            self.start_driver()
            if self.auto_start:
                self.driver.output = 'On'

        if frequency is None:
            frequency = format_and_eval_string(self.frequency, self.task_path,
                                               self.task_database)

        self.driver.frequency_unit = self.unit
        self.driver.frequency = frequency
        self.write_in_database('frequency', frequency)

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(RFSourceSetFrequencyTask, self).check(*args,
                                                                     **kwargs)
        if self.frequency:
            try:
                freq = format_and_eval_string(self.frequency, self.task_path,
                                                   self.task_database)
            except:
                test = False
                traceback[self.task_path + '/' +self.task_name + '-freq'] = \
                    'Failed to eval the frequency formula {}'.format(
                                                                self.frequency)
            self.write_in_database('unit', self.unit)
            self.write_in_database('frequency', freq)
        return test, traceback

class RFSourceSetPowerTask(InstrumentTask):
    """Set the power of the signal delivered by the source.
    """

    power = Str().tag(pref = True)
    auto_start = Bool(False).tag(pref = True)

    driver_list = ['AgilentE8257D']
    task_database_entries = set_default({'power' : -10})
    loopable = True

    @smooth_instr_crash
    def process(self, power = None):
        """
        """
        if not self.driver:
            self.start_driver()
            if self.auto_start:
                self.driver.output = 'On'

        if power is None:
            power = format_and_eval_string(self.power, self.task_path,
                                               self.task_database)

        self.driver.power = power
        self.write_in_database('power', power)

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(RFSourceSetPowerTask, self).check(*args,
                                                                     **kwargs)
        if self.power:
            try:
                power = format_and_eval_string(self.power, self.task_path,
                                                   self.task_database)
            except:
                test = False
                traceback[self.task_path + '/' +self.task_name + '-power'] = \
                    'Failed to eval the frequency power {}'.format(self.power)

            self.write_in_database('power', power)
        return test, traceback

class RFSourceSetOnOffTask(InstrumentTask):
    """Switch on/off the output of the source.
    """

    switch = Str('Off').tag(pref = True)

    driver_list = ['AgilentE8257D']
    task_database_entries = {'output' : 0}
    loopable = True

    @smooth_instr_crash
    def process(self, switch = None):
        """
        """
        if not self.driver:
            self.start_driver()

        if switch is None:
            switch = self.switch

        if switch == 'On' or switch == 1:
            self.driver.output = 'On'
            self.write_in_database('output', 1)
        else:
            self.driver.output = 'Off'
            self.write_in_database('output', 0)

    def check(self, *args, **kwargs):
        """
        """
        self.write_in_database('output', self.switch)
        return super(RFSourceSetOnOffTask, self).check(*args, **kwargs)
