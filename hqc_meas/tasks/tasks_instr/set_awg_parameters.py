# -*- coding: utf-8 -*-
# =============================================================================
# module : set_awg_parameters.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from traceback import format_exc
from inspect import cleandoc
from atom.api import (Value, Str, Int, Bool, List, Dict)

from hqc_meas.utils.atom_util import HasPreferencesAtom, tagged_members
from hqc_meas.tasks.api import (InstrumentTask, InterfaceableTaskMixin,
                                InstrTaskInterface)


class AnalogicalParameters(HasPreferencesAtom):
    """Parameters for the analogical part of the channel.
    """
    amplitude = Str().tag(pref=True, check=True)

    offset = Str().tag(pref=True, check=True)

    rotation = Str().tag(pref=True, check=True)


class LogicalParameters(HasPreferencesAtom):
    """
    """
    low = Str().tag(pref=True, check=True)

    high = Str().tag(pref=True, check=True)

    delay = Str().tag(pref=True, check=True)


class AWGChannelParameters(HasPreferencesAtom):
    """
    """
    active = Str().tag(pref=True, check=True)

    analogical = Int().tag(pref=True)

    logical = Int().tag(pref=True)

    _analogicals = List(AnalogicalParameters)

    _logicals = List(LogicalParameters)

    def checks(self, task):
        """Test all parameters evaluation.

        """
        pass


class SetAWGParametersTask(InterfaceableTaskMixin, InstrumentTask):
    """Build and transfer a pulse sequence to an instrument.

    """

    _channels = Dict()

    def checks(self, *args, **kwargs):
        """
        """
        # TODO handle automatic testing of filed evaluation.
        pass

    def register_preferences(self):
        """
        """
        # TODO handle channels
        pass

    update_preferences_from_members = register_preferences

    def _post_setattr_interface(self, old, new):
        """
        """
        super(SetAWGParametersTask, self)._post_setattr_interface(old, new)
        if new:
            channels = {}
            specs = new.channel_specs
            for i in new.channel_ids:
                channels[i] = AWGChannelParameters(logical=specs[0],
                                                   analogical=specs[1])

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

    driver_list = ['AWG5014B']

    has_view = True

    def perform(self):
        """Set all channels parameters.

        """
        pass


INTERFACES = {'SetAWGParametersTask': [TektroAWGParasInterface]}
