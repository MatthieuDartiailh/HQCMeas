# -*- coding: utf-8 -*-
# =============================================================================
# module : transfer_pulse_sequence_task.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import (Value, Str, Bool, set_default, Enum)
from inspect import cleandoc

from hqc_meas.tasks.api import (InstrumentTask, InterfaceableTaskMixin,
                                InstrTaskInterface)


class TransferPulseSequenceTask(InterfaceableTaskMixin, InstrumentTask):
    """Build and transfer a pulse sequence to an instrument.

    """
    #: Sequence of pulse to compile and transfer to the instrument.
    sequence = Value()

    def register_preferences(self):
        """
        """
        pass

    def update_preferences_from_members(self):
        """
        """
        pass

    @classmethod
    def build_from_config(cls, config, dependencies):
        """
        """
        pass


class AWGTransferInsterface(InstrTaskInterface):
    """
    """
    #: Generic name to use for the sequence (the number of the channel will be
    #: appended automatically).
    sequence_name = Str().tag(pref=True)

    #: Flag indicating whether the transfered sequence should be selected for
    #: execution after transfert.
    select_after_transfer = Bool().tag(pref=True)

    driver_list = ['AWG']

    has_view = True

    interface_database_entries = {'sequence_name': ''}

    def perform(self):
        """
        """
        pass

    def check(self, *args, **kwargs):
        """
        """
        pass
