# -*- coding: utf-8 -*-
# =============================================================================
# module : transfer_pulse_sequence_task.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from traceback import format_exc
from inspect import cleandoc
from atom.api import (Value, Str, Bool, Unicode, Dict)

from hqc_meas.tasks.api import (InstrumentTask, InterfaceableTaskMixin,
                                InstrTaskInterface)


class TransferPulseSequenceTask(InterfaceableTaskMixin, InstrumentTask):
    """Build and transfer a pulse sequence to an instrument.

    """
    #: Sequence path for the case of sequence simply referenced.
    sequence_path = Unicode()

    #: Sequence of pulse to compile and transfer to the instrument.
    sequence = Value()

    #: Global variable to use for the sequence.
    sequence_vars = Dict().tag(pref=True)

    def check(self, *args, **kwargs):
        """Generic check making sure sequence can be compiled.

        """
        test, traceback = super(TransferPulseSequenceTask,
                                self).check(*args, **kwargs)
        err_path = self.task_path + '/' + self.task_name + '_'
        if self.interface and self.sequence:
            if not self.interface.validate_context(self.sequence.context):
                test = False
                mess = 'Invalid context, instrument combination : {}, {}'
                traceback[err_path+'context'] = \
                    mess.format(self.driver, self.sequence.context)

            mess = 'Failed to evaluate {} ({}): {}'
            for k, v in self.sequence_vars.items():
                try:
                    self.format_and_eval_string(v)
                except Exception:
                    test = False
                    traceback[err_path+k] = mess.format(k, v, format_exc())

            if test:
                res, details = self.compile_sequence()
                if not res:
                    test = False
                    mess = cleandoc('''Compilation failed.
                                    Errors : {}.''')
                    traceback[err_path+'compil'] = mess.format(details)

        else:
            test = False
            traceback[err_path+'seq'] = 'No interface or sequence'

        return test, traceback

    def compile_sequence(self):
        """Compile the sequence.

        """
        for k, v in self.sequence_vars.items():
            self.sequence.external_vars[k] = self.format_and_eval_string(v)
        return self.sequence.compile_sequence()

    def answer(self, members, callables):
        """Overriden method to take into account the presence of the sequence.

        """
        infos = super(TransferPulseSequenceTask, self).answer(members,
                                                              callables)
        if not self.sequence_path:
            if 'sequence_path' in infos:
                del infos['sequence_path']
            infos = [infos, self.sequence.walk(members, callables)]

        return infos

    def register_preferences(self):
        """Handle the sequence specific registering in the preferences.

        """
        super(TransferPulseSequenceTask, self).register_preferences()
        if self.sequence_path:
            self.task_preferences['sequence_path'] = self.sequence_path
        elif self.sequence:
            seq = self.sequence
            self.task_preferences['sequence'] = {}
            prefs = seq.preferences_from_members()
            prefs['external_vars'] = \
                repr(dict.fromkeys(seq.external_vars.keys()))
            self.task_preferences['sequence'] = prefs

    update_preferences_from_members = register_preferences

    @classmethod
    def build_from_config(cls, config, dependencies):
        """Rebuild the task and the sequence from a config file.

        """
        builder = cls.mro()[1].build_from_config.__func__
        task = builder(cls, config, dependencies)
        if 'sequence_path' in config:
            path = config['sequence_path']
            builder = dependencies['pulses']['RootSequence']
            conf = dependencies['pulses']['sequences'][path]
            seq = builder.build_from_config(conf, dependencies)
            task.sequence = seq
            task.sequence_path = path
        elif 'sequence' in config:
            builder = dependencies['pulses']['RootSequence']
            conf = config['sequence']
            seq = builder.build_from_config(conf, dependencies)
            task.sequence = seq

        return task


KNOWN_PY_TASKS = [TransferPulseSequenceTask]


class AWGTransferInterface(InstrTaskInterface):
    """Interface for the AWG, handling naming the transfered sequences and
    selecting it.

    """
    #: Generic name to use for the sequence (the number of the channel will be
    #: appended automatically).
    sequence_name = Str().tag(pref=True)
    
    #: Flag indicating whether or not initialisation has been performed.
    initialized = Bool(False)

    #: Flag indicating whether the transfered sequence should be selected for
    #: execution after transfert.
    select_after_transfer = Bool(True).tag(pref=True)

    driver_list = ['AWG5014B']

    has_view = True

    interface_database_entries = {'sequence_name': ''}

    def perform(self):
        """Compile and transfer the sequence into the AWG.

        """
        task = self.task
        if not task.driver:
            task.start_driver()

        seq_name = self.sequence_name if self.sequence_name else 'Sequence'
        res, seqs = task.compile_sequence()
        if not res:
            mess = 'Failed to compile the pulse sequence: missing {}, errs {}'
            raise RuntimeError(mess.format(*seqs))

        initialized = self.initialized
        for ch_id in task.driver.defined_channels:
            if ch_id in seqs:
                self.initialized = task.driver.to_send(seq_name + '_Ch{}'.format(ch_id),
                                    seqs[ch_id], initialized)

        if self.select_after_transfer and (not initialized):
            for ch_id in task.driver.defined_channels:
                ch = task.driver.get_channel(ch_id)
                if ch_id in seqs:
                    ch.select_sequence(seq_name + '_Ch{}'.format(ch_id))
                    ch.output_state = 'ON'
            task.driver.running = 'RUN'

    def check(self, *args, **kwargs):
        """Simply add the sequence name in the database.

        """
        self.task.write_in_database('sequence_name', self.sequence_name)
        return True, {}

    def validate_context(self, context):
        """Validate the context is appropriate for the driver.

        """
        return context.__class__.__name__ == 'AWGContext'
 


INTERFACES = {'TransferPulseSequenceTask': [AWGTransferInterface]}
