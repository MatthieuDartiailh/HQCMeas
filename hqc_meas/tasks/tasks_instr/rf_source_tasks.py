# -*- coding: utf-8 -*-
"""
"""
from atom.api import (Str, Bool, set_default, Enum)
from inspect import cleandoc

from hqc_meas.tasks.api import InstrumentTask
from hqc_meas.tasks.tools.task_decorator import (smooth_instr_crash)
from hqc_meas.tasks.tools.database_string_formatter\
    import format_and_eval_string


class RFSourceSetFrequencyTask(InstrumentTask):
    """Set the frequency of the signal delivered by the source.

    """
    # Target frequency (dynamically evaluated)
    frequency = Str().tag(pref=True)

    # Unit of the frequency
    unit = Enum('GHz', 'MHz', 'kHz', 'Hz').tag(pref=True)

    # Whether to start the source if its output is off.
    auto_start = Bool(False).tag(pref=True)

    driver_list = ['AgilentE8257D']
    task_database_entries = set_default({'frequency': 1.0, 'unit': 'GHz'})
    loopable = True

    @smooth_instr_crash
    def process(self, frequency=None):
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

        return True

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
                traceback[self.task_path + '/' + self.task_name + '-freq'] = \
                    cleandoc('''Failed to eval the frequency
                        formula {}'''.format(self.frequency))
            self.write_in_database('unit', self.unit)
            self.write_in_database('frequency', freq)
        return test, traceback


class RFSourceSetPowerTask(InstrumentTask):
    """Set the power of the signal delivered by the source.

    """
    # Target power (dynamically evaluated)
    power = Str().tag(pref=True)

    # Whether to start the source if its output is off.
    auto_start = Bool(False).tag(pref=True)

    driver_list = ['AgilentE8257D']
    task_database_entries = set_default({'power': -10})
    loopable = True

    @smooth_instr_crash
    def process(self, power=None):
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

        return True

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
                traceback[self.task_path + '/' + self.task_name + '-power'] = \
                    'Failed to eval the frequency power {}'.format(self.power)

            self.write_in_database('power', power)
        return test, traceback


class RFSourceSetOnOffTask(InstrumentTask):
    """Switch on/off the output of the source.

    """
    # Desired state of the output, runtime value can be 0 or 1.
    switch = Str('Off').tag(pref=True)

    driver_list = ['AgilentE8257D']
    task_database_entries = {'output': 0}
    loopable = True

    @smooth_instr_crash
    def process(self, switch=None):
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

        return True

    def check(self, *args, **kwargs):
        """
        """
        self.write_in_database('output', self.switch)
        return super(RFSourceSetOnOffTask, self).check(*args, **kwargs)

KNOWN_PY_TASKS = [RFSourceSetFrequencyTask, RFSourceSetPowerTask,
                  RFSourceSetOnOffTask]
