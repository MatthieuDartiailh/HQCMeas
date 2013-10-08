# -*- coding: utf-8 -*-
"""
"""
from traits.api import (Str, Bool)
from traitsui.api import (View, Group, VGroup, UItem, Label, EnumEditor,
                          LineCompleterEditor)

from textwrap import fill

from .instr_task import InstrumentTask
from .tools.task_decorator import (make_stoppable, make_parallel,
                                   smooth_instr_crash)
from .tools.database_string_formatter import format_and_eval_string

class RFSourceSetFrequencyTask(InstrumentTask):
    """
    """

    frequency = Str(preference = True)
    unit = Str(preference = True)
    auto_start = Bool(False, preference = True)

    driver_list = ['AgilentE8257D']
    task_database_entries = ['frequency', 'unit']
    task_database_entries_default = [1, 'GHZ']
    loopable = True

    loop_view = View(
                    VGroup(
                        UItem('task_name', style = 'readonly'),
                        Group(
                            Label('Driver'), Label('Instr'),
                            Label('Unit'), Label('Auto start'),
                            UItem('selected_driver',
                                editor = EnumEditor(name = 'driver_list'),
                                width = 100),
                            UItem('selected_profile',
                                editor = EnumEditor(name = 'profile_list'),
                                width = 100),
                            UItem('unit',
                                  editor = EnumEditor(values = ['GHZ','MHZ',
                                                                'KHZ','HZ'])
                                ),
                            UItem('auto_start', tooltip = fill('''Should the
                                source be turned on automatically before
                                the measurement starts ?''', 80)
                                ),
                            columns = 4,
                            show_border = True,
                            ),
                        ),
                     )

    def __init__(self, *args, **kwargs):
        super(RFSourceSetFrequencyTask, self).__init__(*args, **kwargs)
        self._define_task_view()

    @make_stoppable
    @make_parallel
    @smooth_instr_crash
    def process(self, frequency = None):
        """
        """
        if not self.driver:
            self.start_driver()
            if self.auto_start:
                self.driver.output = 'On'

        if not frequency:
            frequency = format_and_eval_string(self.frequency, self.task_path,
                                               self.task_database)

        self.driver.frequency_unit = self.unit
        self.driver.fixed_frequency = frequency
        self.write_in_database('frequency', frequency)

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(RFSourceSetFrequencyTask, self).check(*args,
                                                                     **kwargs)
        try:
            freq = format_and_eval_string(self.frequency, self.task_path,
                                               self.task_database)
        except:
            test = False
            traceback[self.task_path + '/' +self.task_name] = \
                'Failed to eval the frequency formula {}'.format(self.frequency)
        self.write_in_database('unit', self.unit)
        self.write_in_database('frequency', freq)
        return test, traceback

    def _list_database_entries(self):
        """
        """
        entries =  self.task_database.list_accessible_entries(self.task_path)
        return entries

    def _define_task_view(self):
        """
        """
        line_completer = LineCompleterEditor(
                             entries_updater = self._list_database_entries)
        view = View(
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
                            UItem('frequency', editor = line_completer),
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
        self.trait_view('task_view', view)


class RFSourceSetPowerTask(InstrumentTask):
    """
    """

    power = Str(preference = True)
    auto_start = Bool(False, preference = True)

    driver_list = ['AgilentE8257D']
    task_database_entries = ['power']
    task_database_entries_default = [1]
    loopable = True

    loop_view = View(
                    VGroup(
                        UItem('task_name', style = 'readonly'),
                        Group(
                            Label('Driver'), Label('Instr'),
                            Label('Auto start'),
                            UItem('selected_driver',
                                editor = EnumEditor(name = 'driver_list'),
                                width = 100),
                            UItem('selected_profile',
                                editor = EnumEditor(name = 'profile_list'),
                                width = 100),
                            UItem('auto_start', tooltip = fill('''Should the
                                source be turned on automatically before
                                the measurement starts ?''', 80)
                                ),
                            columns = 3,
                            show_border = True,
                            ),
                        ),
                     )

    def __init__(self, *args, **kwargs):
        super(RFSourceSetFrequencyTask, self).__init__(*args, **kwargs)
        self._define_task_view()

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

        self.driver.fixed_power = power
        self.write_in_database('power', power)

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(RFSourceSetPowerTask, self).check(*args,
                                                                     **kwargs)
        try:
            power = format_and_eval_string(self.power, self.task_path,
                                               self.task_database)
        except:
            test = False
            traceback[self.task_path + '/' +self.task_name] = \
                'Failed to eval the frequency power {}'.format(self.power)

        self.write_in_database('power', power)
        return test, traceback

    def _list_database_entries(self):
        """
        """
        entries =  self.task_database.list_accessible_entries(self.task_path)
        return entries

    def _define_task_view(self):
        """
        """
        line_completer = LineCompleterEditor(
                             entries_updater = self._list_database_entries)
        view = View(
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
                            UItem('power', editor = line_completer),
                            UItem('auto_start', tooltip = fill('''Should the
                                source be turned on automatically before
                                the measurement starts ?''', 80)
                                ),
                            columns = 4,
                            show_border = True,
                            ),
                        ),
                     )
        self.trait_view('task_view', view)



class RFSourceSetOnOffTask(InstrumentTask):
    """
    """

    switch = Str(preference = True)

    driver_list = ['AgilentE8257D']
    task_database_entries = ['output']
    task_database_entries_default = ['Off']
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

        if switch == 'On' or switch == 1:
            self.driver.output = 'On'
            self.write_in_database('output', 'On')
        else:
            self.driver.output = 'Off'
            self.write_in_database('output', 'Off')

    def check(self, *args, **kwargs):
        """
        """
        self.write_in_database('output', self.switch)
        return super(RFSourceSetOnOffTask, self).check(*args, **kwargs)
