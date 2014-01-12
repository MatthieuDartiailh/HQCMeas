# -*- coding: utf-8 -*-
from atom.api import (Atom, Float, Bool, Str, Property)
from ...atom_util import tagged_members
from ..single_instr_panel import SingleInstrPanel

class SingleInstrPref(Atom):
    """
    """
    title = Str().tag(pref = True)
    check_corrupt = Bool().tag(pref = True)
    corrupt_time = Float(5).tag(pref = True)
    fast_refresh = Bool().tag(pref = True)
    fast_refresh_time = Float(1).tag(pref = True)
    refresh_time = Float(60).tag(pref = True)

    preferences = Property()
    
    _can_check_corrupt = Bool()
    _has_fast_refresh = Bool()
    
    def __init__(self, model_type):
        super(SingleInstrPref, self).__init__()
        self._can_check_corrupt = \
                            bool(model_type._check_driver_state.__func__ is not
                                SingleInstrPanel._check_driver_state.__func__)
        self._has_fast_refresh = \
                    bool(model_type.fast_refresh_members.default_value_mode[1])
    
    @preferences.getter
    def preferences(self):
        return {name : str(getattr(self, name)) 
                for name in tagged_members(self, meta = 'pref')}
                    
PREF_MAPPING = {SingleInstrPanel : SingleInstrPref}