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
import numpy as np

from .instr_task import InstrumentTask
from .tools.task_decorator import (make_stoppable, smooth_instr_crash,
                                   make_wait)
from .tools.database_string_formatter import (format_and_eval_string)
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
                string = self.task_path + '/' + self.task_name + '_' + \
                                                                str(channel)
                traceback[string] = cleandoc(
                '''Channel {} is not defined in the PNA {}, please define it
                yourself and try again.'''.format(channel,
                                                  self.selected_profile))
                channels_present = False

        if not channels_present:
            return False, traceback

        return True, traceback

class PNASetFreqTask(PNATasks):
    """Set the central frequecny to be used for the specified channel.
    """
    channel = Int(1, preference = True)
    frequency = Str(preference = True)

    driver_list = ['AgilentPNA']
    task_database_entries = {'frequency' : 1e9}
    loopable = True

    def __init__(self, *args, **kwargs):
        super(PNASetFreqTask, self).__init__(*args, **kwargs)
        self._define_task_view()

    @make_stoppable
    @smooth_instr_crash
    def process(self, freq = None):
        """
        """
        if not self.driver:
            self.start_driver()
            self.channel_driver = self.driver.get_channel(self.channel)

        if self.channel_driver.owner != self.task_name:
            self.channel_driver.owner = self.task_name

        if not freq:
            freq = format_and_eval_string(self.frequency, self.task_path,
                                         self.task_database)

        self.channel_driver.frequency = freq
        self.write_in_database('frequency', freq)

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(PNASetFreqTask, self).check(*args, **kwargs)
        try:
            format_and_eval_string(self.frequency, self.task_path,
                                         self.task_database)
        except:
            test = False
            traceback[self.task_path + '/' +self.task_name + '-freq'] = \
                'Failed to eval the power formula {}'.format(
                                                        self.frequency)
        return test, traceback

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
                UItem('task_name', style = 'readonly'),
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
                    UItem('frequency', editor = line_completer),
                    columns = 4,
                    ),
                )
        self.trait_view('task_view', view)

class PNASetPowerTask(PNATasks):
    """Set the central power to be used for the specified channel.
    """
    channel = Int(1, preference = True)
    power = Str(preference = True)
    port = Int(1, preference = True)

    driver_list = ['AgilentPNA']
    task_database_entries = {'power' : -10}
    loopable = True

    def __init__(self, *args, **kwargs):
        super(PNASetPowerTask, self).__init__(*args, **kwargs)
        self._define_task_view()

    @make_stoppable
    @smooth_instr_crash
    def process(self, power = None):
        """
        """
        if not self.driver:
            self.start_driver()
            self.channel_driver = self.driver.get_channel(self.channel)

        if self.channel_driver.owner != self.task_name:
            self.channel_driver.owner = self.task_name

        if not power:
            power = format_and_eval_string(self.power, self.task_path,
                                         self.task_database)
        self.channel_driver.port = self.port
        self.channel_driver.power = power
        self.write_in_database('power', power)

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(PNASetPowerTask, self).check(*args, **kwargs)
        try:
            format_and_eval_string(self.power, self.task_path,
                                         self.task_database)
        except:
            test = False
            traceback[self.task_path + '/' +self.task_name + '-power'] = \
                'Failed to eval the power formula {}'.format(
                                                        self.power)
        return test, traceback

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
                UItem('task_name', style = 'readonly'),
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
                    UItem('power', editor = line_completer),
                    columns = 5,
                    ),
                )
        self.trait_view('task_view', view)


class PNASinglePointMeasureTask(PNATasks):
    """Measure the specified parameters. Frequency and power can be set before.
    Wait for any parallel operation before execution.
    """
    channel = Int(1, preference = True)
    measures = List(Str, preference = True)
    measure_format = List(preference = True)

    if_bandwidth = Int(2, preference = True)
    window = Int(1, preference = True)

    driver_list = ['AgilentPNA']
    task_database_entries = {}

    task_view = View(
                    UItem('task_name', style = 'readonly'),
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
                                      are : MLIN, MLOG, PHAS, REAL,
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
                        show_border = True,
                        ),
                    )

    @make_stoppable
    @make_wait()
    @smooth_instr_crash
    def process(self):
        """
        """
        waiting_time = 1.0/self.if_bandwidth
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
            # Avoid the PNA doing stupid things if it was doing a sweep previously
            freq = self.channel_driver.frequency
            power = self.channel_driver.power
            self.channel_driver.sweep_type = 'LIN'
            self.channel_driver.sweep_points = 1
            self.channel_driver.clear_instrument_cache(['frequency', 'power'])
            self.channel_driver.frequency = freq
            self.channel_driver.power = power

            # Check whether or not we are doing the same measures as the ones
            # already defined (avoid losing display optimisation)
            meas_names = ['Ch{}:'.format(self.channel) + measure
                            for measure in self.measures]
            existing_meas = [meas['name']
                    for meas in self.channel_driver.list_existing_measures()]
            if not (all([meas in existing_meas for meas in meas_names])
                    and all([meas in meas_names for meas in existing_meas])):
                clear = True
                self.channel_driver.delete_all_meas()
                for i, meas_name in enumerate(meas_names):
                    self.channel_driver.prepare_measure(meas_name, self.window,
                                                        i+1, clear)
                    clear = False
            if self.if_bandwidth > 5:
                self.channel_driver.sweep_mode = 'CONTinuous'

        if self.if_bandwidth < 5:
            self.driver.fire_trigger(self.channel)
            time.sleep(waiting_time)
            while not self.driver.check_operation_completion():
                time.sleep(0.1*waiting_time)
        else:
            time.sleep(waiting_time)


        for i, measure in enumerate(self.measures):
            meas_name = 'Ch{}:'.format(self.channel) + measure
            self.channel_driver.selected_measure = meas_name
            if self.measure_format[i]:
                data = self.channel_driver.read_formatted_data()[0]
            else:
                data = self.channel_driver.read_raw_data()[0]
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
        entries = {}
        meas_for = []
        for measure in self.measures:
            if len(measure.split(':')) > 1:
                entries[measure] = 1.0
                meas_for.append(True)
            else:
                entries[measure] = 1.0 + 1j
                meas_for.append(False)

        self.measure_format = meas_for
        self.task_database_entries = entries

class PNASweepTask(PNATasks):
    """Measure the specified parameters while sweeping either the frequency or
    the power. Wait for any parallel operation before execution.
    """
    channel = Int(1, preference = True)
    start = Str(preference = True)
    stop = Str(preference = True)
    points = Str(preference = True)
    sweep_type = Enum('Frequency', 'Power', preference = True)
    measures = List(Str, preference = True)

    if_bandwidth = Int(10, preference = True)
    window = Int(1, preference = True)

    driver_list = ['AgilentPNA']
    task_database_entries = {'sweep_data' : np.array([0])}

    def __init__(self, *args, **kwargs):
        super(PNASweepTask, self).__init__(*args, **kwargs)
        self._define_task_view()

    @make_stoppable
    @make_wait()
    @smooth_instr_crash
    def process(self):
        """
        """
        measures_format = self.measures_format()
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

            # Check whether or not we are doing the same measures as the ones
            # already defined (avoid losing display optimisation)
            meas_names = ['Ch{}:'.format(self.channel) + measure
                            for measure in self.measures]
            existing_meas = [meas['name']
                    for meas in self.channel_driver.list_existing_measures()]
            if not (all([meas in existing_meas for meas in meas_names])
                    and all([meas in meas_names for meas in existing_meas])):
                clear = True
                self.channel_driver.delete_all_meas()
                for i, meas_name in enumerate(meas_names):
                    self.channel_driver.prepare_measure(meas_name, self.window,
                                                        i+1, clear)
                    clear = False

        start = format_and_eval_string(self.start, self.task_path,
                                         self.task_database)
        stop = format_and_eval_string(self.stop, self.task_path,
                                         self.task_database)
        points = format_and_eval_string(self.points, self.task_path,
                                         self.task_database)
        self.channel_driver.prepare_sweep(self.sweep_type.upper(), start, stop,
                                          points)

        waiting_time = 1.0/self.if_bandwidth*points
        self.driver.fire_trigger(self.channel)
        time.sleep(waiting_time)
        while not self.driver.check_operation_completion():
            time.sleep(0.1*waiting_time)

        data = [np.linspace(start, stop, points)]
        for i, measure in enumerate(self.measures):
            meas_name = 'Ch{}:'.format(self.channel) + measure
            if measures_format[i]:
                data.append(
                    self.channel_driver.read_formatted_data(meas_name))
            else:
                data.append(self.channel_driver.read_raw_data(meas_name))
        names = [self.sweep_type] + self.measures
        final_arr = np.rec.fromarrays(data, names = names)
        self.write_in_database('sweep_data', final_arr)

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(PNASweepTask, self).check(*args, **kwargs)
        try:
            format_and_eval_string(self.start, self.task_path,
                                         self.task_database)
        except:
            test = False
            traceback[self.task_path + '/' + self.task_name + '-start'] = \
                'Failed to eval the start formula {}'.format(
                                                        self.start)
        try:
             format_and_eval_string(self.stop, self.task_path,
                                             self.task_database)
        except:
            test = False
            traceback[self.task_path + '/' +self.task_name + '-stop'] = \
                'Failed to eval the stop formula {}'.format(
                                                        self.stop)
        try:
            format_and_eval_string(self.points, self.task_path,
                                         self.task_database)
        except:
            test = False
            traceback[self.task_path + '/' +self.task_name + '-step'] = \
                'Failed to eval the points formula {}'.format(
                                                        self.points)

        data = [np.array([0.0,1.0])] + \
                    [np.array([0.0,1.0]) for meas in self.measures]
        names = [self.sweep_type] + self.measures
        final_arr = np.rec.fromarrays(data, names = names)

        self.write_in_database('sweep_data', final_arr)
        return test, traceback

    @on_trait_change('channel')
    def _update_channels(self, new):
        self.channels = [new]

    def measures_format(self):
        """
        """
        entries = self.measures
        meas_for = []
        for measure in entries:
            if len(measure.split(':')) > 1:
                meas_for.append(True)
            else:
                meas_for.append(False)

        return meas_for

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
                UItem('task_name', style = 'readonly'),
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
                                      are : MLIN, MLOG, PHAS, REAL,
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
                    show_border = True,
                    ),
                )
        self.trait_view('task_view', view)
