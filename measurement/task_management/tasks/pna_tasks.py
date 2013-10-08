# -*- coding: utf-8 -*-
#==============================================================================
# module : pna_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""

"""

from traits.api import (Str, Int, List, on_trait_change, Enum)
from traitsui.api import (View, Group, VGroup, UItem, Label, EnumEditor, HGroup,
                          ListInstanceEditor, LineCompleterEditor)

import time, os
from inspect import cleandoc
from configobj import ConfigObj
from textwrap import fill

from .instr_task import InstrumentTask
from .tools.task_decorator import (make_stoppable, smooth_instr_crash,
                                   make_wait)
from .tools.database_string_formatter import get_formatted_string
from ...instruments.profiles import PROFILES_DIRECTORY_PATH
from ...instruments.drivers import DRIVERS
from ...instruments.drivers.driver_tools import InstrIOError

class PNATasks(InstrumentTask):
    """
    """
    channels = List(Int, preference = True)

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

class PNASetFreqTask(PNATasks):
    """
    """
    channel = Int(1, preference = True)
    value = Str(preference = True)

    driver_list = ['AgilentPNA']
    task_database_entries = ['frequency']
    task_database_entries_default = [1e9]

    def __init__(self, *args, **kwargs):
        super(PNASetFreqTask, self).__init__(*args, **kwargs)
        self._define_task_view()

    @make_stoppable
    @smooth_instr_crash
    def process(self):
        """
        """
        if not self.driver:
            self.start_driver()
            self.channel_driver = self.driver.get_channel(self.channel)

        if self.channel_driver.owner != self.task_name:
            self.channel_driver.owner = self.task_name

        freq = eval(get_formatted_string(self.value, self.task_path,
                                         self.task_database))
        self.channel_driver.frequency = freq
        self.write_in_database('frequency', freq)

    @on_trait_change('channel')
    def _update_channels(self, new):
        self.channels = [new]

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
                Group(
                    Label('Driver'), Label('Instr'),
                    Label('Channel'), Label('Freq (Hz)'),
                    UItem('selected_driver',
                        editor = EnumEditor(name = 'driver_list'),
                        width = 100),
                    UItem('selected_profile',
                        editor = EnumEditor(name = 'profile_list'),
                        width = 100),
                    UItem('channel'),
                    UItem('value', editor = line_completer),
                    columns = 4,
                    ),
                )
        self.trait_view('task_view', view)

class PNASetPowerTask(PNATasks):
    """
    """
    channel = Int(1, preference = True)
    value = Str(preference = True)
    port = Int(1, preference = True)

    driver_list = ['AgilentPNA']
    task_database_entries = ['power']
    task_database_entries_default = [10]

    def __init__(self, *args, **kwargs):
        super(PNASetPowerTask, self).__init__(*args, **kwargs)
        self._define_task_view()

    @make_stoppable
    @smooth_instr_crash
    def process(self):
        """
        """
        if not self.driver:
            self.start_driver()
            self.channel_driver = self.driver.get_channel(self.channel)

        if self.channel_driver.owner != self.task_name:
            self.channel_driver.owner = self.task_name

        power = eval(get_formatted_string(self.value, self.task_path,
                                         self.task_database))
        self.channel_driver.port = self.port
        self.channel_driver.power = power
        self.write_in_database('power', power)

    @on_trait_change('channel')
    def _update_channels(self, new):
        self.channels = [new]

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
                Group(
                    Label('Driver'), Label('Instr'),
                    Label('Channel'), Label('Port'), Label('Power (dBm)'),
                    UItem('selected_driver',
                        editor = EnumEditor(name = 'driver_list'),
                        width = 100),
                    UItem('selected_profile',
                        editor = EnumEditor(name = 'profile_list'),
                        width = 100),
                    UItem('channel', width = 50), UItem('port', width = 50),
                    UItem('value', editor = line_completer),
                    columns = 5,
                    ),
                )
        self.trait_view('task_view', view)


class PNASinglePointMeasureTask(PNATasks):
    """
    """
    channel = Int(1, preference = True)
    measures = List(Str, preference = True)
    measure_format = List(preference = True)

    if_bandwidth = Int(2, preference = True)
    window = Int(1, preference = True)

    driver_list = ['AgilentPNA']
    task_database_entries = []
    task_database_entries_default = []

    task_view = View(
                    VGroup(
                        Group(
                            Label('Driver'), Label('Instr'),
                            UItem('selected_driver',
                                editor = EnumEditor(name = 'driver_list'),
                                width = 100),
                            UItem('selected_profile',
                                editor = EnumEditor(name = 'profile_list'),
                                width = 100),
                            columns = 2,
                            ),
                        HGroup(
                            VGroup(
                                UItem('measures', style = 'custom',
                                      editor = ListInstanceEditor(),
                                      tooltip = fill(cleandoc('''Measure should
                                      be described by the parameter to measure
                                      and followed by ':' and then the format in
                                      which to diplay and read them, if omitted,
                                      the measurement will return the complex
                                      number. ex : 'S21:PHAS.'''), 80) + '\n' +\
                                      fill(cleandoc('''Available formats
                                      are : MLIN, MLOG, PHAS, REA,
                                      IMAG'''),80),
                                      ),
                            label = 'Measures',
                            show_border = True,
                            ),
                            Group(
                                Label('Channel'), UItem('channel'),
                                Label('IF (Hz)'), UItem('if_bandwidth'),
                                Label('Window'), UItem('window'),
                                columns = 2),
                            ),
                        ),
                    )

    @make_stoppable
    @make_wait
    @smooth_instr_crash
    def process(self):
        """
        """
        waiting_time = 1.05*1/self.if_bandwidth
        if not self.driver:
            self.start_driver()
            self.channel_driver = self.driver.get_channel(self.channel)

        if self.driver.owner != self.task_name:
            self.driver.owner = self.task_name
            self.driver.set_all_chanel_to_hold()
            self.driver.trigger_scope = 'CURRent'
            if self.if_bandwidth > 5:
                self.driver.trigger_source = 'IMMediate'
            else:
                self.driver.trigger_source = 'MANual'

        if self.channel_driver.owner != self.task_name:
            self.channel_driver.owner = self.task_name
            self.channel_driver.if_bandwidth = self.if_bandwidth
            self.channel_driver.sweep_points = 1
            clear = True
            self.channel_driver.delete_all_meas()
            for i, measure in enumerate(self.measures):
                meas_name = 'Ch{}:'.format(self.channel) + measure
                self.channel_driver.prepare_measure(meas_name, self.window, i+1,
                                                    clear)
                clear = False

        if self.if_bandwidth < 5:
            self.driver.fire_trigger(self.channel)
            time.sleep(waiting_time)
            while not self.driver.check_operation_completion():
                time.sleep(0.1*waiting_time)
        else:
            time.sleep(waiting_time)


        for i, measure in enumerate(self.measures):
            meas_name = 'Ch{}:'.format(self.channel) + measure
            if self.measure_format[i]:
                data = self.channel_driver.read_formatted_data(meas_name)[0]
            else:
                data = self.channel_driver.read_raw_data(meas_name)[0]
            self.write_in_database(measure, data)

    @on_trait_change('channel')
    def _update_channels(self, new):
        """
        """
        self.channels = [new]

    @on_trait_change('measures[]')
    def _post_measures_update(self):
        """
        """
        entries_def = []
        entries = self.measures
        meas_for = []
        for measure in entries:
            if len(measure.split(':')) > 1:
                entries_def.append(1)
                meas_for.append(True)
            else:
                entries_def.append(1+1j)
                meas_for.append(False)

        self.measure_format = meas_for
        self.task_database_entries_default = entries_def
        self.task_database_entries = entries

class PNAFreqSweepTask(PNATasks):
    """
    """
    channel = Int(1, preference = True)
    start = Str(preference = True)
    stop = Str(preference = True)
    points = Str(preference = True)
    sweep_type = Enum('Frequency', 'Power', preference = True)
    measures = List(Str, preference = True)
    measure_format = List(preference = True)

    if_bandwidth = Int(10, preference = True)
    window = Int(1, preference = True)

    driver_list = ['AgilentPNA']
    task_database_entries = []
    task_database_entries_default = []

    def __init__(self, *args, **kwargs):
        super(PNAFreqSweepTask, self).__init__(*args, **kwargs)
        self._define_task_view()

    @make_stoppable
    @make_wait
    @smooth_instr_crash
    def process(self):
        """
        """
        waiting_time = 1.05*1/self.if_bandwidth
        if not self.driver:
            self.start_driver()
            self.channel_driver = self.driver.get_channel(self.channel)

        if self.driver.owner != self.task_name:
            self.driver.owner = self.task_name
            self.driver.set_all_chanel_to_hold()
            self.driver.trigger_scope = 'CURRent'
            self.driver.trigger_source = 'MANual'

        if self.channel_driver.owner != self.task_name:
            self.channel_driver.owner = self.task_name
            self.channel_driver.if_bandwidth = self.if_bandwidth
            clear = True
            for i, measure in enumerate(self.measures):
                meas_name = 'Ch{}_'.format(self.channel) + measure
                self.channel_driver.preapre_measure(meas_name, self.window, i+1,
                                                    clear)
                clear = False

        start = eval(get_formatted_string(self.start, self.task_path,
                                         self.task_database))
        stop = eval(get_formatted_string(self.stop, self.task_path,
                                         self.task_database))
        points = eval(get_formatted_string(self.points, self.task_path,
                                         self.task_database))
        self.channel_driver.prepare_sweep(self.type.upper(), start, stop,
                                          points)
        waiting_time = 1/self.if_bandwidth*points

        self.driver.fire_trigger(self.channel)
        time.sleep(waiting_time)
        while not self.driver.check_operation_completion():
            time.sleep(0.01*waiting_time)

        for i, measure in enumerate(self.measures):
            meas_name = 'Ch{}_'.format(self.channel) + measure
            if self.measure_format[i]:
                data = self.channel_driver.read_formatted_data(meas_name)
            else:
                data = self.channel_driver.read_raw_data(meas_name)
            self.write_in_database(measure, data)


    @on_trait_change('channel')
    def _update_channels(self, new):
        self.channels = [new]

    @on_trait_change('measures')
    def _update_database_entries(self):
        entries_def = []
        entries = self.measures
        for measure in entries:
            if len(measure.split(':')) > 1:
                entries_def.append(1)
            else:
                entries_def.append(1+1j)

        self.task_database_entries_default = entries_def
        self.task_database_entries = entries

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
                    Group(
                        Label('Driver'), Label('Instr'),
                        UItem('selected_driver',
                            editor = EnumEditor(name = 'driver_list'),
                            width = 100),
                        UItem('selected_profile',
                            editor = EnumEditor(name = 'profile_list'),
                            width = 100),
                        columns = 2,
                        ),
                    Group(
                        Label('Type'), Label('Start'),
                        Label('Stop'), Label('Points'),
                        UItem('sweep_type'),
                        UItem('start', editor = line_completer),
                        UItem('stop', editor = line_completer),
                        UItem('points', editor = line_completer),
                        columns = 4,
                        ),
                    HGroup(
                        VGroup(
                            UItem('measures', style = 'custom',
                                  editor = ListInstanceEditor(),
                                  tooltip = fill(cleandoc('''Measure should
                                      be described by the parameter to measure
                                      and followed by ':' and then the format in
                                      which to diplay and read them, if omitted,
                                      the measurement will return the complex
                                      number. ex : 'S21:PHAS.'''), 80) + '\n' +\
                                      fill(cleandoc('''Available formats
                                      are : MLIN, MLOG, PHAS, REA,
                                      IMAG'''),80),
                                  ),
                        label = 'Measures',
                        show_border = True,
                        ),
                        Group(
                            Label('Channel'), UItem('channel'),
                            Label('IF (Hz)'), UItem('if_bandwidth'),
                            Label('Window'), UItem('window'),
                            columns = 2),
                        ),
                    ),
                )
        self.trait_view('task_view', view)