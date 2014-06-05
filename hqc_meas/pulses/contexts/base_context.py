# -*- coding: utf-8 -*-
#==============================================================================
# module : base_context.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import Enum, Str
from hqc_meas.utils.atom_util import HasPrefAtom


class BaseContext(HasPrefAtom):
    """
    """

    time_unit = Enum('mus', 's', 'ms', 'ns')

    context_class = Str().tag(pref=True)

    def compile_sequence(self, pulses, **kwargs):
        """

        """
        pass

    def _default_context_class(self):
        """ Default value the context class member.

        """
        return type(self).__name__
