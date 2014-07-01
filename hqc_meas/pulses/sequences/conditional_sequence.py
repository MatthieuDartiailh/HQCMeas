# -*- coding: utf-8 -*-
#==============================================================================
# module : conditional_sequence.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import Str, set_default

from ..pulses import Sequence
from .entry_eval import eval_entry


class ConditionalSequence(Sequence):
    """ Sequence whose child items will be included only if a condition is met.

    """
    condition = Str().tag(pref=True)

    linkable_vars = set_default(['condition'])

    def compile_sequence(self, sequence_locals, missing_locals, errors):
        """ Compile the sequence in a flat list of pulses.

        The list of pulse will be not empty only if the condition specified
        for the sequence is met.

        Parameters
        ----------
        sequence_locals : dict
            Dictionary of local variables.

        missings : set
            Set of unfound local variables.

        errors : dict
            Dict of the errors which happened when performing the evaluation.

        Returns
        -------
        flag : bool
            Boolean indicating whether or not the evaluation succeeded.

        pulses : list
            List of pulses in which all the string entries have been evaluated.

        """
        cond = None
        try:
            cond = bool(eval_entry(self.condition,
                                   sequence_locals, missing_locals))
        except Exception as e:
            errors['{}_'.format(self.index) + 'condition'] = repr(e)

        if cond is None:
            return False, []

        local = '{}_'.format(self.index) + 'condition'
        sequence_locals[local] = cond

        if cond:
            return super(ConditionalSequence,
                         self).compile_sequence(sequence_locals,
                                                missing_locals, errors)

        else:
            return True, []
