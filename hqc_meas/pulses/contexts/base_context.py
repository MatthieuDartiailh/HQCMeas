# -*- coding: utf-8 -*-
#==============================================================================
# module : base_context.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import Str
from hqc_meas.utils.atom_util import HasPrefAtom


class BaseContext(HasPrefAtom):
    """
    """

    time_unit = Str('mus')
