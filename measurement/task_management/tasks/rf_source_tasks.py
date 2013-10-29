# -*- coding: utf-8 -*-
"""
"""
from traits.api import (Str, Bool)
from traitsui.api import (View, Group, VGroup, UItem, Label, EnumEditor,
                          LineCompleterEditor)

from textwrap import fill

from .instr_task import InstrumentTask
from .tools.task_decorator import (make_stoppable, smooth_instr_crash)
from .tools.database_string_formatter import format_and_eval_string

class RFSourceSetFrequencyTask(InstrumentTask):
    """Set the frequency of the signal delivered by the source.
    """

    frequency = Str(preference = True)
    unit = Str(preference = True)
    auto_start = Bool(False, preference = True)

    driver_list = ['AgilentE8257D']
    task_database_entries = {'frequency' : 1.0, 'unit' : 'GHZ'}
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
    """Set the power of the signal delivered by the source.
    """

    power = Str(preference = True)
    auto_start = Bool(False, preference = True)

    driver_list = ['AgilentE8257D']
    task_database_entries = {'power' : -10}
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
        super(RFSourceSetPowerTask, self).__init__(*args, **kwargs)
        self._define_task_view()

    @make_stoppable
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
    """Switch on/off the output of the source.
    """

    switch = Str(preference = True)

    driver_list = ['AgilentE8257D']
    task_database_entries = {'output' : 'Off'}
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
    loop_view = View(
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
                            columns = 3,
                            show_border = True,
                            ),
                        ),
                     )

    @make_stoppable
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
