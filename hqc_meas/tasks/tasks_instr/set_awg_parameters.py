# -*- coding: utf-8 -*-
# =============================================================================
# module : set_awg_parameters.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from traceback import format_exc
from ast import literal_eval
from itertools import chain
from atom.api import (Str, Int, List, Dict)

from hqc_meas.utils.atom_util import HasPrefAtom, tagged_members
from hqc_meas.tasks.api import (InstrumentTask, InterfaceableTaskMixin,
                                InstrTaskInterface)


class AnalogicalParameters(HasPrefAtom):
    """Parameters for one analogical port of the channel.

    """
    parameter1 = Str().tag(pref=True, check=True)

    parameter2 = Str().tag(pref=True, check=True)

    parameter3 = Str().tag(pref=True, check=True)


class LogicalParameters(HasPrefAtom):
    """Parameters for one logical port of the channel.

    """
    parameter1 = Str().tag(pref=True, check=True)

    parameter2 = Str().tag(pref=True, check=True)

    parameter3 = Str().tag(pref=True, check=True)


class AWGChannelParameters(HasPrefAtom):
    """Parameters for one channel of the AWG.

    """
    active = Str().tag(pref=True, check=True)

    analogical = Int().tag(pref=True)

    logical = Int().tag(pref=True)

    analogicals = List(AnalogicalParameters)

    logicals = List(LogicalParameters)

    def init_parameters(self):
        """Create blanck parameters objects.

        """
        self.analogicals = [AnalogicalParameters()
                            for i in range(self.analogical)]
        self.logicals = [LogicalParameters()
                         for i in range(self.logical)]

    def check(self, task):
        """Test all parameters evaluation.

        """
        traceback = {}
        i = 0
        kind = 'Analogical{}_'
        for p in chain(self.analogicals, self.logicals):
            if i == self.analogical:
                kind = 'Logical{}_'
            for n in tagged_members(p, 'check'):
                val = getattr(p, n)
                if not val:
                    continue
                try:
                    task.format_and_eval_string(val)
                except Exception:
                    mess = 'Failed to eval {} : {}'
                    traceback[kind.format(i) + n] = mess.format(val,
                                                                format_exc())

            i += 1

        return not bool(traceback), traceback

    def preferences_from_members(self):
        """Overwritten to handle channels saving.

        """
        pref = super(AWGChannelParameters, self).preferences_from_members()
        for i, para in enumerate(self.logicals):
            pref['logical_{}'.format(i)] = para.preferences_from_members()
        for i, para in enumerate(self.analogicals):
            pref['analogical_{}'.format(i)] = para.preferences_from_members()
        return pref

    @classmethod
    def build_from_config(cls, config):
        """
        """
        new = cls(active=config.get('active', ''),
                  analogical=int(config['analogical']),
                  logical=int(config['logical']))

        s = 'logical_{}'
        new.logicals = [LogicalParameters(**config[s.format(i)])
                        for i in range(new.logical)]

        s = 'analogical_{}'
        new.analogicals = [AnalogicalParameters(**config[s.format(i)])
                           for i in range(new.analogical)]

        return new


class SetAWGParametersTask(InterfaceableTaskMixin, InstrumentTask):
    """Set the parameters of the different channels of the AWG.
    """

    _channels = Dict()

    def check(self, *args, **kwargs):
        """Automatically test all parameters evaluation.

        """
        test, traceback = super(SetAWGParametersTask,
                                self).check(*args, **kwargs)
        for id, ch in self._channels.items():
            res, tr = ch.check(self)
            aux = {'Ch{}_{}'.format(id, err): val for err, val in tr.items()}
            traceback.update(aux)
            test &= res

        return test, traceback

    def register_preferences(self):
        """Overriden to handle channels.

        """
        super(SetAWGParametersTask, self).register_preferences()
        for id, ch in self._channels.items():
            prefs = ch.preferences_from_members()
            self.task_preferences['channel_{}'.format(repr(id))] = prefs

    update_preferences_from_members = register_preferences

    @classmethod
    def build_from_config(cls, config, dependencies):
        """Handle rebuilding the channel dict.

        """
        new = super(SetAWGParametersTask, cls).build_from_config(config,
                                                                 dependencies)
        channels = {}
        chs = {k: literal_eval(k[8:])
               for k in config if k.startswith('channel_')}
        for ch in chs:
            ch_obj = AWGChannelParameters.build_from_config(config[ch])
            channels[chs[ch]] = ch_obj

        new._channels = channels

        return new

    def _post_setattr_interface(self, old, new):
        """Create empty channels when an interface is selected.

        """
        super(SetAWGParametersTask, self)._post_setattr_interface(old, new)
        if new:
            channels = {}
            specs = new.channels_specs
            for i in new.channels_ids:
                channels[i] = AWGChannelParameters(logical=specs[i][0],
                                                   analogical=specs[i][1])
                channels[i].init_parameters()

            self._channels = channels

KNOWN_PY_TASKS = [SetAWGParametersTask]


class AWGParasInterface(InstrTaskInterface):
    """
    """
    #: List of channel ids for this interface.
    channels_ids = []

    #: Specification for each id (number of logical ports,
    #: number of analogical ports)
    channels_specs = {}


class TektroAWGParasInterface(AWGParasInterface):
    """Interface for the AWG, handling naming the transfered sequences and
    selecting it.

    """
    channels_ids = [1, 2, 3, 4]

    channels_specs = {1: (2, 1), 2: (2, 1), 3: (2, 1), 4: (2, 1)}

    driver_list = ['AWG5014B']

    has_view = True

    def perform(self):
        """Set all channels parameters.

        """
        task = self.task
        if not task.driver:
            task.start_driver()

        if task.driver.owner != task.task_name:
            task.driver.owner = task.task_name

        for ch_id in self.channels_ids:
            ch_dr = task.driver.get_channel(ch_id)
            ch = task._channels[ch_id]
            if ch.active:
                state = task.format_and_eval_string(ch.active)
                ch_dr.output_state = state

            analogic = ch.analogicals[0]
            if analogic.parameter1:
                amp = task.format_and_eval_string(analogic.parameter1)
                ch_dr.vpp = amp
            if analogic.parameter2:
                off = task.format_and_eval_string(analogic.parameter2)
                ch_dr.offset = off
            if analogic.parameter3:
                ph = task.format_and_eval_string(analogic.parameter3)
                ch_dr.phase = ph

            logical1 = ch.logicals[0]
            if logical1.parameter1:
                low = task.format_and_eval_string(logical1.parameter1)
                ch_dr.marker1_low_voltage = low
            if logical1.parameter2:
                high = task.format_and_eval_string(logical1.parameter2)
                ch_dr.marker1_high_voltage = high
            if logical1.parameter3:
                de = task.format_and_eval_string(logical1.parameter3)
                ch_dr.marker1_delay = de

            logical2 = ch.logicals[1]
            if logical2.parameter1:
                low = task.format_and_eval_string(logical2.parameter1)
                ch_dr.marker2_low_voltage = low
            if logical2.parameter2:
                high = task.format_and_eval_string(logical2.parameter2)
                ch_dr.marker2_high_voltage = high
            if logical2.parameter3:
                de = task.format_and_eval_string(logical2.parameter3)
                ch_dr.marker2_delay = de

INTERFACES = {'SetAWGParametersTask': [TektroAWGParasInterface]}
