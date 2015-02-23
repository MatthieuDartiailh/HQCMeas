# -*- coding: utf-8 -*-
# =============================================================================
# module : set_awg_parameters.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from traceback import format_exc
from itertools import chain
from atom.api import (Str, Int, List, Dict)

from hqc_meas.utils.atom_util import HasPreferencesAtom, tagged_members
from hqc_meas.tasks.api import (InstrumentTask, InterfaceableTaskMixin,
                                InstrTaskInterface)


class AnalogicalParameters(HasPreferencesAtom):
    """Parameters for one analogical port of the channel.

    """
    amplitude = Str().tag(pref=True, check=True)

    offset = Str().tag(pref=True, check=True)

    phase = Str().tag(pref=True, check=True)


class LogicalParameters(HasPreferencesAtom):
    """Parameters for one logical port of the channel.

    """
    low = Str().tag(pref=True, check=True)

    high = Str().tag(pref=True, check=True)

    delay = Str().tag(pref=True, check=True)


class AWGChannelParameters(HasPreferencesAtom):
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
                         for i in range(self.analogical)]

    def checks(self, task):
        """Test all parameters evaluation.

        """
        traceback = {}
        for k, p in chain(self.analogicals.items(), self.logicals.items()):
            for n in tagged_members(p, 'check'):
                val = getattr(p, n)
                if not val:
                    continue
                try:
                    task.format_and_eval_string(val)
                except Exception:
                    mess = 'Failed to eval {} : {}'
                    traceback[k + '_' + n] = mess.format(val, format_exc())

        return not bool(traceback), traceback

    def preferences_from_members(self):
        """Overwritten to handle channels saving.

        """
        pref = super(AWGChannelParameters, self).preferences_from_members()
        for i, para in enumerate(self.logicals):
            pref['logical_{}'.format(i)] = para.preferences_from_members()
        for i, para in enumerate(self.analogicals):
            pref['analogical_{}'.format(i)] = para.preferences_from_members()

    @classmethod
    def build_from_config(cls, config):
        """
        """
        new = cls(active=config.get('active', ''),
                  analogical=int(config['analogical']),
                  logical=int(config['logical']))

        s = 'logical_{}'
        new.logicals = [LogicalParameters(config[s.format(i)])
                        for i in range(new.logical)]

        s = 'analogical_{}'
        new.analogicals = [AnalogicalParameters(config[s.format(i)])
                           for i in range(new.analogical)]

        return new


class SetAWGParametersTask(InterfaceableTaskMixin, InstrumentTask):
    """Set the parameters of the different channels of the AWG.
    """

    _channels = Dict()

    def checks(self, *args, **kwargs):
        """Automatically test all parameters evaluation.

        """
        test, traceback = super(SetAWGParametersTask,
                                self).checks(*args, **kwargs)
        for id, ch in self._channels.items():
            res, tr = ch.checks(self)
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
            self.task_preferences['channel_{}'.format(id)] = prefs

    update_preferences_from_members = register_preferences

    @classmethod
    def build_from_config(cls, config, dependencies):
        """Handle rebuilding the channel dict.

        """
        new = super(SetAWGParametersTask, cls).build_from_config(config,
                                                                 dependencies)
        chs = {k: k[8:] for k in config if k.startswith('channel_')}
        for ch in chs:
            ch_obj = AWGChannelParameters.build_from_config(config[ch])
            new._channels[chs[ch]] = ch_obj

        return new

    def _post_setattr_interface(self, old, new):
        """Create empty channels when an interface is selected.

        """
        super(SetAWGParametersTask, self)._post_setattr_interface(old, new)
        if new:
            channels = {}
            specs = new.channel_specs
            for i in new.channel_ids:
                channels[i] = AWGChannelParameters(logical=specs[0],
                                                   analogical=specs[1])
                channels[i].init_parameters()

            self._channels = channels

KNOWN_PY_TASKS = [SetAWGParametersTask]


class AWGParasInterface(InstrTaskInterface):
    """
    """
    #: List of channel ids for this interface.
    channel_ids = []

    #: Specification for each id (number of logical ports,
    #: number of analogical ports)
    channel_specs = {}


class TektroAWGParasInterface(AWGParasInterface):
    """Interface for the AWG, handling naming the transfered sequences and
    selecting it.

    """
    channel_ids = [1, 2, 3, 4]

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

        for ch_id in self.channel_ids:
            ch_dr = task.driver.get_channel(ch_id)
            ch = task._channels[ch_id]
            if ch.active:
                state = task.format_and_eval_string(ch.active)
                ch_dr.output_state = state

            analogic = ch.analogical[0]
            if analogic.amplitude:
                amp = task.format_and_eval_string(analogic.amplitude)
                ch_dr.vpp = amp
            if analogic.offset:
                off = task.format_and_eval_string(analogic.offset)
                ch_dr.offset = off
            if analogic.phase:
                ph = task.format_and_eval_string(analogic.phase)
                ch_dr.phase = ph

            logical1 = ch.logical[0]
            if logical1.low:
                low = task.format_and_eval_string(logical1.low)
                ch_dr.marker1_low_voltage = low
            if logical1.high:
                high = task.format_and_eval_string(logical1.high)
                ch_dr.marker1_high_voltage = high
            if logical1.delay:
                de = task.format_and_eval_string(logical1.delay)
                ch_dr.marker1_delay = de

            logical2 = ch.logical[1]
            if logical1.low:
                low = task.format_and_eval_string(logical2.low)
                ch_dr.marker2_low_voltage = low
            if logical1.high:
                high = task.format_and_eval_string(logical2.high)
                ch_dr.marker2_high_voltage = high
            if logical1.delay:
                de = task.format_and_eval_string(logical2.delay)
                ch_dr.marker2_delay = de

INTERFACES = {'SetAWGParametersTask': [TektroAWGParasInterface]}
