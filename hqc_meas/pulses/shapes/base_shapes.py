# -*- coding: utf-8 -*-
#==============================================================================
# module : base_shapes.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import (Int, Instance, Str, Enum, ForwardTyped, Float,
                      Typed, Bool)

from hqc_meas.utils.atom_util import HasPrefAtom

class AbstractShape(HasPrefAtom):
    """
    """

    def compute(self, time, unit):
        """
        """
        pass
