# -*- coding: utf-8 -*-
from atom.api import (Atom, Float, Bool, Str)
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
    
    def preferences(self):
        return {name : getattr(self, name) 
                for name in tagged_members(self, meta = 'pref')}
                    
PREF_MAPPING = {SingleInstrPanel : SingleInstrPref}