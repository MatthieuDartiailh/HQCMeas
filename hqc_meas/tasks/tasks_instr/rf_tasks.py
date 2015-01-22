# -*- coding: utf-8 -*-
# =============================================================================
# module : rf_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import (Str, Bool, set_default, Enum)
from inspect import cleandoc

from hqc_meas.tasks.api import (InstrumentTask, InterfaceableTaskMixin)

CONVERSION_FACTORS = {'GHz': {'Hz': 1e9, 'kHz': 1e6, 'MHz': 1e3, 'GHz': 1},
                      'MHz': {'Hz': 1e6, 'kHz': 1e3, 'MHz': 1, 'GHz': 1e-3},
                      'kHz': {'Hz': 1e3, 'kHz': 1, 'MHz': 1e-3, 'GHz': 1e-6},
                      'Hz': {'Hz': 1, 'kHz': 1e-3, 'MHz': 1e-6, 'GHz': 1e-9}}


class SetRFFrequencyTask(InterfaceableTaskMixin, InstrumentTask):
    """Set the frequency of the signal delivered by a RF source.

    """
    # Target frequency (dynamically evaluated)
    frequency = Str().tag(pref=True)

    # Unit of the frequency
    unit = Enum('GHz', 'MHz', 'kHz', 'Hz').tag(pref=True)

    # Whether to start the source if its output is off.
    auto_start = Bool(False).tag(pref=True)

    task_database_entries = set_default({'frequency': 1.0, 'unit': 'GHz'})
    loopable = True
    driver_list = ['AgilentE8257D', 'AnritsuMG3694', 'LabBrickLMS103']

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(SetRFFrequencyTask, self).check(*args,
                                                                **kwargs)
        if self.frequency:
            try:
                freq = self.format_and_eval_string(self.frequency)
                self.write_in_database('frequency', freq)
            except Exception as e:
                test = False
                traceback[self.task_path + '/' + self.task_name + '-freq'] = \
                    cleandoc('''Failed to eval the frequency
                        formula {}: {}'''.format(self.frequency, e))

        self.write_in_database('unit', self.unit)

        return test, traceback

    def i_perform(self, frequency=None):
        """

        """
        if not self.driver:
            self.start_driver()
            if self.auto_start:
                self.driver.output = 'On'

        if frequency is None:
            frequency = self.format_and_eval_string(self.frequency)

        self.driver.frequency_unit = self.unit
        self.driver.frequency = frequency
        self.write_in_database('frequency', frequency)

    def convert(self, frequency, unit):
        """ Convert a frequency to the given unit.

        Parameters
        ----------
        frequency : float
            Frequency expressed in the task unit

        unit : {'Hz', 'kHz', 'MHz', 'GHz'}
            Unit in which to express the result

        Returns
        -------
        converted_frequency : float

        """
        return frequency*CONVERSION_FACTORS[self.unit][unit]


class SetRFPowerTask(InterfaceableTaskMixin, InstrumentTask):
    """Set the power of the signal delivered by the source.

    """
    # Target power (dynamically evaluated)
    power = Str().tag(pref=True)

    # Whether to start the source if its output is off.
    auto_start = Bool(False).tag(pref=True)

    task_database_entries = set_default({'power': -10})
    loopable = True
    driver_list = ['AgilentE8257D','AnritsuMG3694','LabBrickLMS103']

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(SetRFPowerTask, self).check(*args,
                                                            **kwargs)
        if self.power:
            try:
                power = self.format_and_eval_string(self.power)
                self.write_in_database('power', power)
            except Exception as e:
                test = False
                traceback[self.task_path + '/' + self.task_name + '-power'] = \
                    'Failed to eval the power {}: {}'.format(self.power, e)

        return test, traceback

    def i_perform(self, power=None):
        """

        """
        if not self.driver:
            self.start_driver()
            if self.auto_start:
                self.driver.output = 'On'

        if power is None:
            power = self.format_and_eval_string(self.power)

        self.driver.power = power
        self.write_in_database('power', power)


class SetRFOnOffTask(InterfaceableTaskMixin, InstrumentTask):
    """Switch on/off the output of the source.

    """
    # Desired state of the output, runtime value can be 0 or 1.
    switch = Str('Off').tag(pref=True)

    task_database_entries = set_default({'output': 0})
    loopable = True
    driver_list = ['AgilentE8257D','AnritsuMG3694','LabBrickLMS103']

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(SetRFOnOffTask, self).check(*args, **kwargs)

        if self.switch:
            try:
                switch = self.format_and_eval_string(self.switch)
                self.write_in_database('output', switch)
            except Exception as e:
                mess = 'Failed to eval the output state {}: {}'
                traceback[self.task_path + '/' + self.task_name + '-switch'] =\
                    mess.format(self.switch, e)
                return False, traceback

            if switch not in ('Off', 'On', 0, 1):
                test = False
                traceback[self.task_path + '/' + self.task_name + '-switch'] =\
                    '{} is not an acceptable value.'.format(self.switch)

        return test, traceback

    def i_perform(self, switch=None):
        """

        """
        if not self.driver:
            self.start_driver()

        if switch is None:
            switch = self.format_and_eval_string(self.switch)

        if switch == 'On' or switch == 1:
            self.driver.output = 'On'
            self.write_in_database('output', 1)
        else:
            self.driver.output = 'Off'
            self.write_in_database('output', 0)


KNOWN_PY_TASKS = [SetRFFrequencyTask, SetRFPowerTask,
                  SetRFOnOffTask]
