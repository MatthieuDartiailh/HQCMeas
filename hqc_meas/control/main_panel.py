# -*- coding: utf-8 -*-
from atom.api import (Bool, Str, Unicode, List, Dict, Typed, observe)
from enaml.widgets.api import DockItemEvent
import os

from ..atom_util import PrefAtom, tagged_members
from ..instruments.instrument_manager import InstrumentManager

MODULE_PATH = os.path.dirname(__file__)

class MainPanelModel(PrefAtom):
    """
    """
    instr_manager = Typed(InstrumentManager, ())
    available_profiles = List(Unicode())
    used_profiles = Dict(Unicode())
    measure_profile = List(Unicode())
    
    dock_event = Typed(DockItemEvent)
    
    def __init__(self):
        super(MainPanelModel, self).__init__()
        
        
    def save_panel_state(self, dock_area):
        pass
    
    def load_panel_state(self):
        pass
    
    def release_drivers(self, profiles):
        """
        """
        used = self.used_profiles
        for profile in profiles:
            if profile in used:
                panel = used[profile]
                panel.release_driver()
    
    @observe('dock_event')
    def _control_panel_closed(self, change):
        """
        """
        # must release driver and remove from used_profiles
        pass
    
    @observe('instr_manager.instrs')
    def _profiles_updated(self, change):
        """
        """
        instrs = change['value']
        used = set(self.used_profiles.keys() + self.measure_profile)
        self.available_profiles = [instrs[p] for p in instrs
                                    if instrs[p] not in used]