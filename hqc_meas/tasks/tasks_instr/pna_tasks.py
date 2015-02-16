# -*- coding: utf-8 -*-
# =============================================================================
# module : pna_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import (Str, Int, Bool, Enum, set_default, Tuple,
                              ContainerList, Value)

import time
import re
from inspect import cleandoc
import numpy as np

from hqc_meas.tasks.api import InstrumentTask, InstrTaskInterface
from hqc_meas.instruments.driver_tools import InstrIOError


def check_channels_presence(task, channels, *args, **kwargs):
    """ Check that all the channels are correctly defined on the PNA.

    """
    if kwargs.get('test_instr'):
        run_time = task.root_task.run_time
        traceback = {}
        if task.selected_profile and run_time:
            config = run_time['profiles'].get(task.selected_profile)
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

                mes = '''Channel {} is not defined in the PNA {}, please define
                    it yourself and try again.'''
                traceback[string] = cleandoc(mes.format(channel,
                                                        task.selected_profile)
                                             )

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
            power = task.format_and_eval_string(task.power)

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

    channel_driver = Value()

    def check(self, *args, **kwargs):
        """ Add checking for channels to the base tests.

        """
        test, traceback = super(SingleChannelPNATask, self).check(*args,
                                                                  **kwargs)
        c_test, c_trace = check_channels_presence(self, [self.channel],
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

    wait = set_default({'activated': True, 'wait': ['instr']})

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
            self.channel_driver.clear_cache(['frequency', 'power'])
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
            self.write_in_database('_'.join(self.measures[i]), data)

    def check(self, *args, **kwargs):
        """

        """
        test, traceback = super(PNASinglePointMeasureTask,
                                self).check(*args, **kwargs)

        pattern = re.compile('S[1-4][1-4]')
        for i, meas in enumerate(self.measures):
            match = pattern.match(meas[0])
            if not match:
                path = self.task_path + '/' + self.task_name
                path += '_Meas_{}'.format(i)
                traceback[path] = 'Unvalid parameter : {}'.format(meas[0])
                test = False

        return test, traceback

    def _observe_measures(self, change):
        """
        """
        entries = {}
        for measure in change['value']:
            if measure[1]:
                entries['_'.join(measure)] = 1.0
            else:
                entries[measure[0]] = 1.0 + 1j

        self.task_database_entries = entries


class PNASweepTask(SingleChannelPNATask):
    """Measure the specified parameters while sweeping either the frequency or
    the power. Measure are saved in an array with named fields : Frequency or
    Power and then 'Measure'_'Format' (S21_MLIN, S33 if Raw)

    Wait for any parallel operation before execution.

    """
    channel = Int(1).tag(pref=True)

    start = Str().tag(pref=True)

    stop = Str().tag(pref=True)

    points = Str().tag(pref=True)

    sweep_type = Enum('','Frequency', 'Power').tag(pref=True)

    measures = ContainerList(Tuple()).tag(pref=True)

    if_bandwidth = Int(0).tag(pref=True)

    window = Int(1).tag(pref=True)

    wait = set_default({'activated': True, 'wait': ['instr']})
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
            if self.if_bandwidth>0:
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
        current_Xaxis = self.channel_driver.sweep_x_axis
        if self.start:
            start = self.format_and_eval_string(self.start)
        else:
            start = current_Xaxis[0]*1e9
        if self.stop:
            stop = self.format_and_eval_string(self.stop)
        else:
            stop = current_Xaxis[-1]*1e9
        if self.points:
            points = self.format_and_eval_string(self.points)
        else:
            points = len(current_Xaxis)
        if self.sweep_type:
            self.channel_driver.prepare_sweep(self.sweep_type.upper(), start,
                                              stop, points)
        else:
            if self.channel_driver.sweep_type.upper() == 'LIN':
                self.channel_driver.prepare_sweep('FREQUENCY',
                                                  start, stop, points)
            elif self.channel_driver.sweep_type.upper() == 'POW':
                 self.channel_driver.prepare_sweep('POWER',
                                                  start, stop, points)

        waiting_time = self.channel_driver.sweep_time
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

        names = [self.sweep_type] + ['_'.join(measure)
                                     for measure in self.measures]
        final_arr = np.rec.fromarrays(data, names=names)
        self.write_in_database('sweep_data', final_arr)

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(PNASweepTask, self).check(*args, **kwargs)

        pattern = re.compile('S[1-4][1-4]')
        for i, meas in enumerate(self.measures):
            match = pattern.match(meas[0])
            if not match:
                path = self.task_path + '/' + self.task_name
                path += '_Meas_{}'.format(i)
                traceback[path] = 'Unvalid parameter : {}'.format(meas[0])
                test = False
        if self.start:
            try:
                self.format_and_eval_string(self.start)
            except:
                test = False
                traceback[self.task_path + '/' + self.task_name + '-start'] = \
                    'Failed to eval the start formula {}'.format(self.start)
        if self.stop:
            try:
                self.format_and_eval_string(self.stop)
            except:
                test = False
                traceback[self.task_path + '/' + self.task_name + '-stop'] = \
                    'Failed to eval the stop formula {}'.format(self.stop)
        if self.points:
            try:
                self.format_and_eval_string(self.points)
            except:
                test = False
                traceback[self.task_path + '/' + self.task_name + '-step'] = \
                    'Failed to eval the points formula {}'.format(self.points)

        data = [np.array([0.0, 1.0])] + \
            [np.array([0.0, 1.0]) for meas in self.measures]
        names = [self.sweep_type] + ['_'.join(meas) for meas in self.measures]
        final_arr = np.rec.fromarrays(data, names=names)

        self.write_in_database('sweep_data', final_arr)
        return test, traceback

class PNAGetTraces(InstrumentTask):
    """ Get the traces that are displayed right now (no new acquisition).

    The list of traces to be measured must be entered in the following format
    ch1,tr1;ch2,tr2;ch3,tr3;...
    ex: 1,1;1,3 for ch1, tr1 and ch1, tr3

    """

    tracelist = Str('1,1').tag(pref=True)
    already_measured = Bool(False).tag(pref=True)

    driver_list = ['AgilentPNA']
    task_database_entries = set_default({'sweep_data': {}})

    def perform(self):
        traces = self.tracelist.split(';')
        if not self.driver:
            self.start_driver()

        tr_data = {}

        if not self.already_measured:
            for i in range(1,30):
                if str(i)+',' in self.tracelist:
                    self.average_channel(i)

        for trace in traces:
            c_nb, t_nb = trace.split(',')
            tr_data[trace] = self.get_trace(int(c_nb), int(t_nb))

        self.write_in_database('sweep_data', tr_data)

    def average_channel(self, channelnb):
        """ Performs the averaging of a channel

        """
        channel_driver = self.driver.get_channel(channelnb)
        channel_driver.run_averaging()

    def get_trace(self, channelnb, tracenb):
        """ Get the trace that is displayed right now (no new acquisition)
        on channel and tracenb.

        """

        channel_driver = self.driver.get_channel(channelnb)

        try:
            channel_driver.tracenb = tracenb
        except:
            raise ValueError(cleandoc('''The trace {} does not exist on channel
                                      {}: '''.format(tracenb, channelnb)))

        measname = channel_driver.selected_measure
        data = channel_driver.sweep_x_axis
        complexdata = channel_driver.read_raw_data(measname)* \
                np.exp(2*np.pi*1j*data*channel_driver.electrical_delay)
        aux = [data, complexdata.real, complexdata.imag,
                np.absolute(complexdata),
                np.unwrap(np.angle(complexdata))]

        return np.rec.fromarrays(aux, names=['Freq (GHz)', measname+' real',
                    measname+' imag',  measname+' abs',  measname+' phase' ])

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(PNAGetTraces, self).check(*args, **kwargs)

        traces = self.tracelist.split(';')
        sweep_data = {}
        for trace in traces:
            data = [np.array([0.0, 1.0]), np.array([1.0, 2.0])]
            sweep_data[trace] = np.rec.fromarrays(data, names=['a', 'b'])

        self.write_in_database('sweep_data', sweep_data)
        return test, traceback




KNOWN_PY_TASKS = [PNASinglePointMeasureTask,
                  PNASweepTask,
                  PNAGetTraces]
