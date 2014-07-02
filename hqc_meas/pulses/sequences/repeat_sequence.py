# -*- coding: utf-8 -*-
# =============================================================================
# module : repeat_sequence.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from atom.api import Str, set_default

from ..pulses import Sequence


class RepeatSequence(Sequence):
    """ Sequence whose child items will be included multiple times.

    """
    iter_duration = Str().tag(pref=True)

    iter_number = Str().tag(pref=True)

    linkable_vars = set_default(['iter_start', 'iter_stop'])

    def compile_sequence(self, sequence_locals):
        """

        """
        # TODO later will require some use of deepcopy.
        pass
