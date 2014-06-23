# -*- coding: utf-8 -*-
#==============================================================================
# module : pna_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from atom.api import (Str, Int, Enum, set_default,
                      Tuple, ContainerList, Value)

import time
from inspect import cleandoc
import numpy as np

from hqc_meas.tasks.api import InstrumentTask, InstrTaskInterface
from hqc_meas.instruments.drivers.driver_tools import InstrIOError


def check_channels_presence(task, channels, *args, **kwargs):
    """ Check that all the channels are correctly defined on the PNA.

    """
    if kwargs.get('test_instr'):
        run_time = task.root_task.run_time
        traceback = {}
        if task.selected_profile and run_time:
            config = run_time['profiles'][task.selected_profile]
            if not config:
                return False, traceback
        else:
            return False, traceback

        if run_time and task.selected_driver in run_time['drivers']:
            driver_class = run_time['drivers'][task.selected_driver]
        else:
            return False, traceback

        try:
            instr = driver_class(config)
        except InstrIOError:
            return False, traceback

        channels_present = True
        for channel in channels:
            if channel not in instr.defined_channels:
                string = task.task_path + '/' + task.task_name +\
                    '_' + str(channel)

                traceback[string] = cleandoc(
                    '''Channel {} is not defined in the PNA {}, please define
                    it yourself and try again.'''.format(channel,
                    task.selected_profile))

                channels_present = False

        return channels_present, traceback

    else:
        return True, {}


class PNASetRFFrequencyInterface(InstrTaskInterface):
    """Set the central frequecny to be used for the specified channel.

    """
    # Id of the channel whose central frequency should be set.
    channel = Int(1).tag(pref=True)

    # Driver for the channel.
    channel_driver = Value()

    driver_list = ['AgilentPNA']

    has_view = True

    def perform(self, frequency=None):
        """
        """
        task = self.task
        if not task.driver:
            task.start_driver()
            self.channel_driver = task.driver.get_channel(self.channel)

        task.driver.owner = task.task_name
        self.channel_driver.owner = task.task_name

        if frequency is None:
            frequency = task.format_and_eval_string(task.frequency)
            frequency = task.convert(frequency, 'Hz')

        self.channel_driver.frequency = frequency
        task.write_in_database('frequency', frequency)

    def check(self, *args, **kwargs):
        """

        """
        task = self.task
        return check_channels_presence(task, [self.channel], *args, **kwargs)


class PNASetRFPowerInterface(InstrTaskInterface):
    """Set the central power to be used for the specified channel.

    """
    # Id of the channel whose central frequency should be set.
    channel = Int(1).tag(pref=True)

    # Driver for the channel.
    channel_driver = Value()

    # Port whose output power should be set.
    port = Int(1).tag(pref=True)

    driver_list = ['AgilentPNA']

    has_view = True

    def perform(self, power=None):
        """
        """
        task = self.task
        if not task.driver:
            task.start_driver()
            self.channel_driver = task.driver.get_channel(self.channel)

        task.driver.owner = task.task_name
        self.channel_driver.owner = task.task_name

        if power is None:
            power = self.format_and_eval_string(self.power)

        self.channel_driver.port = self.port
        self.channel_driver.power = power
        task.write_in_database('power', power)

    def check(self, *args, **kwargs):
        """

        """
        task = self.task
        return check_channels_presence(task, [self.channel], *args, **kwargs)


INTERFACES = {'SetRFFrequencyTask': [PNASetRFFrequencyInterface],
              'SetRFPowerTask': [PNASetRFPowerInterface]}


class SingleChannelPNATask(InstrumentTask):
    """ Helper class managing the notion of channel in the PNA.

    """
    # Id of the channel to use.
    channel = Int(1).tag(pref=True)

    def check(self, *args, **kwargs):
        """ Add checking for channels to the base tests.

        """
        test, traceback = super(SingleChannelPNATask, self).check(*args,
                                                                  **kwargs)
        c_test, c_trace = check_channels_presence(self.task, [self.channel],
                                                  *args, **kwargs)

        traceback.update(c_trace)
        return test and c_test, traceback


class PNASinglePointMeasureTask(SingleChannelPNATask):
    """Measure the specified parameters. Frequency and power can be set before.

    Wait for any parallel operation before execution.

    """
    channel = Int(1).tag(pref=True)
    measures = ContainerList(Tuple()).tag(pref=True)

    if_bandwidth = Int(2).tag(pref=True)
    window = Int(1).tag(pref=True)

    driver_list = ['AgilentPNA']

    wait = set_default({'wait': ['instr']})  # Wait on instr pool by default.

    def perform(self):
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
            if self.if_bandwidth >= 5:
                self.driver.trigger_source = 'IMMediate'
            else:
                self.driver.trigger_source = 'MANual'

        meas_names = ['Ch{}:'.format(self.channel) + ':'.join(measure)
                      for measure in self.measures]

        if self.channel_driver.owner != self.task_name:
            self.channel_driver.owner = self.task_name
            self.channel_driver.if_bandwidth = self.if_bandwidth
            # Avoid the PNA doing stupid things if it was doing a sweep
            # previously
            freq = self.channel_driver.frequency
            power = self.channel_driver.power
            self.channel_driver.sweep_type = 'LIN'
            self.channel_driver.sweep_points = 1
            self.channel_driver.clear_instrument_cache(['frequency', 'power'])
            self.channel_driver.frequency = freq
            self.channel_driver.power = power

            # Check whether or not we are doing the same measures as the ones
            # already defined (avoid losing display optimisation)
            measures = self.channel_driver.list_existing_measures()
            existing_meas = [meas['name'] for meas in measures]

            if not (all([meas in existing_meas for meas in meas_names])
                    and all([meas in meas_names for meas in existing_meas])):
                clear = True
                self.channel_driver.delete_all_meas()
                for i, meas_name in enumerate(meas_names):
                    self.channel_driver.prepare_measure(meas_name, self.window,
                                                        i+1, clear)
                    clear = False
            if self.if_bandwidth >= 5:
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
            if self.measures[i][1]:
                data = self.channel_driver.read_formatted_data()[0]
            else:
                data = self.channel_driver.read_raw_data()[0]
            self.write_in_database(':'.join(self.measures[i]), data)

        return True

    def _observe_measures(self, change):
        """
        """
        entries = {}
        for measure in change['value']:
            if measure[1]:
                entries[':'.join(measure)] = 1.0
            else:
                entries[measure[0]] = 1.0 + 1j

        self.task_database_entries = entries


class PNASweepTask(SingleChannelPNATask):
    """Measure the specified parameters while sweeping either the frequency or
    the power.

    Wait for any parallel operation before execution.

    """
    channel = Int(1).tag(pref=True)

    start = Str().tag(pref=True)

    stop = Str().tag(pref=True)

    points = Str().tag(pref=True)

    sweep_type = Enum('Frequency', 'Power').tag(pref=True)

    measures = ContainerList(Tuple()).tag(pref=True)

    if_bandwidth = Int(10).tag(pref=True)

    window = Int(1).tag(pref=True)

    wait = set_default({'wait': ['instr']})  # Wait on instr pool by default.
    driver_list = ['AgilentPNA']
    task_database_entries = set_default({'sweep_data': np.array([0])})

    def perform(self):
        """
        """
        if not self.driver:
            self.start_driver()
            self.channel_driver = self.driver.get_channel(self.channel)

        if self.driver.owner != self.task_name:
            self.driver.owner = self.task_name
            self.driver.set_all_chanel_to_hold()
            self.driver.trigger_scope = 'CURRent'
            self.driver.trigger_source = 'MANual'

        meas_names = ['Ch{}:'.format(self.channel) + ':'.join(measure)
                      for measure in self.measures]

        if self.channel_driver.owner != self.task_name:
            self.channel_driver.owner = self.task_name
            self.channel_driver.if_bandwidth = self.if_bandwidth

            # Check whether or not we are doing the same measures as the ones
            # already defined (avoid losing display optimisation)
            measures = self.channel_driver.list_existing_measures()
            existing_meas = [meas['name'] for meas in measures]

            if not (all([meas in existing_meas for meas in meas_names])
                    and all([meas in meas_names for meas in existing_meas])):
                clear = True
                self.channel_driver.delete_all_meas()
                for i, meas_name in enumerate(meas_names):
                    self.channel_driver.prepare_measure(meas_name, self.window,
                                                        i+1, clear)
                    clear = False

        start = self.format_and_eval_string(self.start)
        stop = self.format_and_eval_string(self.stop)
        points = self.format_and_eval_string(self.points)
        self.channel_driver.prepare_sweep(self.sweep_type.upper(), start, stop,
                                          points)

        waiting_time = 1.0/self.if_bandwidth*points
        self.driver.fire_trigger(self.channel)
        time.sleep(waiting_time)
        while not self.driver.check_operation_completion():
            time.sleep(0.1*waiting_time)

        data = [np.linspace(start, stop, points)]
        for i, meas_name in enumerate(meas_names):
            if self.measures[i][1]:
                data.append(
                    self.channel_driver.read_formatted_data(meas_name))
            else:
                data.append(self.channel_driver.read_raw_data(meas_name))

        names = [self.sweep_type] + meas_names
        final_arr = np.rec.fromarrays(data, names=names)
        self.write_in_database('sweep_data', final_arr)

        return True

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(PNASweepTask, self).check(*args, **kwargs)
        try:
            self.format_and_eval_string(self.start)
        except:
            test = False
            traceback[self.task_path + '/' + self.task_name + '-start'] = \
                'Failed to eval the start formula {}'.format(self.start)
        try:
            self.format_and_eval_string(self.stop)
        except:
            test = False
            traceback[self.task_path + '/' + self.task_name + '-stop'] = \
                'Failed to eval the stop formula {}'.format(self.stop)
        try:
            self.format_and_eval_string(self.points)
        except:
            test = False
            traceback[self.task_path + '/' + self.task_name + '-step'] = \
                'Failed to eval the points formula {}'.format(self.points)

        data = [np.array([0.0, 1.0])] + \
            [np.array([0.0, 1.0]) for meas in self.measures]
        names = [self.sweep_type] + [':'.join(meas) for meas in self.measures]
        final_arr = np.rec.fromarrays(data, names=names)

        self.write_in_database('sweep_data', final_arr)
        return test, traceback


KNOWN_PY_TASKS = [PNASinglePointMeasureTask,
                  PNASweepTask]
