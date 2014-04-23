# -*- coding: utf-8 -*-
#==============================================================================
# module : pna_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""

"""
# TODO fix PNATAsks check and PEP8
from atom.api import (Atom, Str, Int, List, observe, Enum, set_default, Bool,
                      Typed, ContainerList)

import time
import os
from inspect import cleandoc
from configobj import ConfigObj
import numpy as np

from ..instr_task import InstrumentTask
from ..tools.task_decorator import (smooth_instr_crash)
from ..tools.database_string_formatter import (format_and_eval_string)
from hqc_meas.instruments.drivers.driver_tools import InstrIOError


class PNATasks(InstrumentTask):
    """ Helper class managing the notion of channel in the PNA.

    """
    # List of necessary channels.
    channels = List(Int()).tag(pref=True)

    def check(self, *args, **kwargs):
        """ Add checking for channels to the base tests.

        """
        traceback = {}
        full_path = self.profile_dict[self.selected_profile]

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
    channel = Int(1).tag(pref=True)
    frequency = Str().tag(pref=True)

    driver_list = ['AgilentPNA']
    task_database_entries = set_default({'frequency': 1e9})
    loopable = True

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

    @observe('channel')
    def _update_channels(self, change):
        self.channels = [change['value']]

class PNASetPowerTask(PNATasks):
    """Set the central power to be used for the specified channel.
    """
    channel = Int(1).tag(pref = True)
    power = Str().tag(pref = True)
    port = Int(1).tag(pref = True)

    driver_list = ['AgilentPNA']
    task_database_entries = set_default({'power' : -10})
    loopable = True

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

    @observe('channel')
    def _update_channels(self, change):
        self.channels = [change['value']]

class PNAMeasure(Atom):
    """
    """
    measure = Str()

class PNASinglePointMeasureTask(PNATasks):
    """Measure the specified parameters. Frequency and power can be set before.
    Wait for any parallel operation before execution.
    """
    channel = Int(1).tag(pref = True)
    measures = ContainerList(Typed(PNAMeasure)).tag(pref=True)
    measure_format = List(Bool()).tag(pref = True)

    if_bandwidth = Int(2).tag(pref = True)
    window = Int(1).tag(pref = True)

    driver_list = ['AgilentPNA']

    def __init__(self, **kwargs):
        super(PNASinglePointMeasureTask, self).__init__(**kwargs)
        self.make_wait(wait = ['instr'])

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

        meas_names = ['Ch{}:'.format(self.channel) + measure.measure
                            for measure in self.measures]

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


        for i, meas_name in enumerate(meas_names):
            self.channel_driver.selected_measure = meas_name
            if self.measure_format[i]:
                data = self.channel_driver.read_formatted_data()[0]
            else:
                data = self.channel_driver.read_raw_data()[0]
            self.write_in_database(measure, data)

    @observe('channel')
    def _update_channels(self, change):
        """
        """
        self.channels = [change['value']]

    @observe('measures')
    def _post_measures_update(self, change):
        """
        """
        entries = {}
        meas_for = []
        for measure in change['value']:
            if len(measure.split(':')) > 1:
                entries[measure.measure] = 1.0
                meas_for.append(True)
            else:
                entries[measure.measure] = 1.0 + 1j
                meas_for.append(False)

        self.measure_format = meas_for
        self.task_database_entries = entries

class PNASweepTask(PNATasks):
    """Measure the specified parameters while sweeping either the frequency or
    the power. Wait for any parallel operation before execution.
    """
    channel = Int(1).tag(pref = True)
    start = Str().tag(pref = True)
    stop = Str().tag(pref = True)
    points = Str().tag(pref = True)
    sweep_type = Enum('Frequency', 'Power').tag(pref = True)
    measures = ContainerList(Str()).tag(pref = True)

    if_bandwidth = Int(10).tag(pref = True)
    window = Int(1).tag(pref = True)

    driver_list = ['AgilentPNA']
    task_database_entries = set_default({'sweep_data' : np.array([0])})

    def __init__(self, **kwargs):
        super(PNASweepTask, self).__init__(**kwargs)
        self.make_wait(wait = ['instr'])

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

        meas_names = ['Ch{}:'.format(self.channel) + measure.measure
                            for measure in self.measures]

        if self.channel_driver.owner != self.task_name:
            self.channel_driver.owner = self.task_name
            self.channel_driver.if_bandwidth = self.if_bandwidth

            # Check whether or not we are doing the same measures as the ones
            # already defined (avoid losing display optimisation)
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
        for i, meas_name in enumerate(meas_names):
            if measures_format[i]:
                data.append(
                    self.channel_driver.read_formatted_data(meas_name))
            else:
                data.append(self.channel_driver.read_raw_data(meas_name))
        names = [self.sweep_type] + meas_names
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

    @observe('channel')
    def _update_channels(self, change):
        self.channels = [change['value']]

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

KNOWN_PY_TASKS = [PNASetFreqTask, PNASetPowerTask, PNASinglePointMeasureTask,
                  PNASweepTask]