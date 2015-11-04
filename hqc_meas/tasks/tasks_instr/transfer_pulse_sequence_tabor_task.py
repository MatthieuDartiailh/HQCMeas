# -*- coding: utf-8 -*-
# =============================================================================
# module : transfer_pulse_sequence_tabor_task.py
# author : Matthieu Dartiailh & Nathanael Cottet
# license : MIT license
# =============================================================================
"""
"""

from hqc_meas.tasks.api import (InstrTaskInterface)


class TaborTransferInterface(InstrTaskInterface):
    """Interface for the Tabor, handling naming the transfered sequences and
    selecting it.

    """
    #: Generic name to use for the sequence (the number of the channel will be
    #: appended automatically).
    # sequence_name = Str().tag(pref=True)

    #: Flag indicating whether the transfered sequence should be selected for
    #: execution after transfert.
    # select_after_transfer = Bool().tag(pref=True)

    driver_list = ['TaborAWG']

    has_view = False

    # interface_database_entries = {'sequence_name': ''}

    def perform(self):
        """Compile and transfer the sequence into the AWG.

        """
        task = self.task
        if not task.driver:
            task.start_driver()

        # seq_name = self.sequence_name if self.sequence_name else 'Sequence'
        res, seqs = task.compile_sequence()
        if not res:
            mess = 'Failed to compile the pulse sequence: missing {}, errs {}'
            raise RuntimeError(mess.format(*seqs))

        for ch_id in task.driver.defined_channels:
            if ch_id in seqs:
                task.driver.to_send(seqs[ch_id], ch_id)
#                while task.driver.is_ready < 1:
#                    print task.driver.is_ready
#                    pass


    def check(self, *args, **kwargs):
        """Generic check making sure sequence can be compiled.

        """
        return True, {}

    def validate_context(self, context):
        """Validate the context is appropriate for the driver.

        """
        return context.__class__.__name__ == 'TABORContext'


INTERFACES = {'TransferPulseSequenceTask': [TaborTransferInterface]}

