# -*- coding: utf-8 -*-
# =============================================================================
# module : pulses/item.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from atom.api import (Int, Str, List, Bool, ForwardTyped)

from hqc_meas.utils.atom_util import HasPrefAtom


def root():
    from .base_sequences import RootSequence
    return RootSequence


class Item(HasPrefAtom):
    """ Base component a pulse sequence.

    """
    # --- Public API ----------------------------------------------------------

    #: Index identifying the item inside the sequence.
    index = Int()

    #: Flag to disable a particular item.
    enabled = Bool(True).tag(pref=True)

    #: Class of the item to use when rebuilding a sequence.
    item_class = Str().tag(pref=True)

    #: Name of the variable which can be referenced in other items.
    linkable_vars = List()

    #: Reference to the root sequence.
    root = ForwardTyped(root)

    # --- Private API ---------------------------------------------------------

    def _default_item_class(self):
        """ Default value for the item_class member.

        """
        return self.__class__.__name__
