# -*- coding: utf-8 -*-
"""
"""
from traits.api import (Str, Float, Bool)
from traitsui.api import (View, Group, VGroup, UItem, Label, EnumEditor)

from textwrap import fill

from .instr_task import InstrumentTask
from .tools.task_decorator import (make_stoppable, make_parallel,
                                   smooth_instr_crash)

class RFSourceSetFrequencyTask(InstrumentTask):
    """
    """

    frequency = Float(preference = True)
    unit = Str(preference = True)
    auto_start = Bool(False, preference = True)

    driver_list = ['AgilentE8257D']
    task_database_entries = ['frequency', 'unit']
    loopable = True

    task_view = View(
                    VGroup(
                        UItem('task_name', style = 'readonly'),
                        Group(
                            Label('Driver'), Label('Instr'), Label('Freq'),
                            Label('Unit'), Label('Auto start'),
                            UItem('selected_driver',
                                editor = EnumEditor(name = 'driver_list'),
                                width = 100),
                            UItem('selected_profile',
                                editor = EnumEditor(name = 'profile_list'),
                                width = 100),
                            UItem('frequency'),
                            UItem('unit',
                                  editor = EnumEditor(values = ['GHZ','MHZ',
                                                                'KHZ','HZ'])
                                ),
                            UItem('auto_start', tooltip = fill('''Should the
                                source be turned on automatically before
                                the measurement starts ?''', 80)
                                ),
                            columns = 5,
                            show_border = True,
                            ),
                        ),
                     )

    @make_stoppable
    @make_parallel
    @smooth_instr_crash
    def process(self, frequency = None):
        """
        """
        if not self.driver:
            self.start_driver()
            if self.auto_start:
                self.driver.set_output_on_off('On')

        if not frequency:
            frequency = self.frequency

        self.driver.set_fixed_frequency(frequency, self.unit)
        self.write_in_database('frequency', frequency)

    def check(self, *args, **kwargs):
        """
        """
        self.write_in_database('unit', self.unit)
        self.write_in_database('frequency', self.frequency)
        return super(RFSourceSetFrequencyTask, self).check(*args, **kwargs)


class RFSourceSetPowerTask(InstrumentTask):
    """
    """

    power = Float(preference = True)
    auto_start = Bool(False, preference = True)

    driver_list = ['AgilentE8257D']
    task_database_entries = ['power']
    loopable = True

    task_view = View(
                    VGroup(
                        UItem('task_name', style = 'readonly'),
                        Group(
                            Label('Driver'), Label('Instr'), Label('Power'),
                            Label('Auto start'),
                            UItem('selected_driver',
                                editor = EnumEditor(name = 'driver_list'),
                                width = 100),
                            UItem('selected_profile',
                                editor = EnumEditor(name = 'profile_list'),
                                width = 100),
                            UItem('power'),
                            UItem('auto_start', tooltip = fill('''Should the
                                source be turned on automatically before
                                the measurement starts ?''', 80)
                                ),
                            columns = 4,
                            show_border = True,
                            ),
                        ),
                     )

    @make_stoppable
    @make_parallel
    @smooth_instr_crash
    def process(self, power = None):
        """
        """
        if not self.driver:
            self.start_driver()
            if self.auto_start:
                self.driver.set_output_on_off('On')

        if not power:
            power = self.power

        self.driver.set_fixed_power(power)
        self.write_in_database('power', power)

    def check(self, *args, **kwargs):
        """
        """
        self.write_in_database('power', self.power)
        return super(RFSourceSetPowerTask, self).check(*args, **kwargs)



class RFSourceSetOnOffTask(InstrumentTask):
    """
    """

    switch = Str(preference = True)

    driver_list = ['AgilentE8257D']
    task_database_entries = ['switch']
    loopable = True

    task_view = View(
                    VGroup(
                        UItem('task_name', style = 'readonly'),
                        Group(
                            Label('Driver'), Label('Instr'), Label('Switch'),
                            UItem('selected_driver',
                                editor = EnumEditor(name = 'driver_list'),
                                width = 100),
                            UItem('selected_profile',
                                editor = EnumEditor(name = 'profile_list'),
                                width = 100),
                            UItem('switch',
                                editor = EnumEditor(values =  ['On', 'Off']),
                                width = 100),
                            columns = 3,
                            show_border = True,
                            ),
                        ),
                     )

    @make_stoppable
    @make_parallel
    @smooth_instr_crash
    def process(self, switch = None):
        """
        """
        if not self.driver:
            self.start_driver()

        if not switch:
            switch = self.switch

        if switch == 'On':
            self.driver.switch_on_off('On')
            self.write_in_database('switch', 'On')
        else:
            self.driver.switch_on_off('Off')
            self.write_in_database('switch', 'Off')

    def check(self, *args, **kwargs):
        """
        """
        self.write_in_database('switch', self.switch)
        return super(RFSourceSetOnOffTask, self).check(*args, **kwargs)
