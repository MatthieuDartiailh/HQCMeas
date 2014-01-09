# -*- coding: utf-8 -*-
from atom.api import (ContainerList, Unicode, List, Dict, Typed, Instance, 
                      Bool, observe)
import os

from ..atom_util import PrefAtom, tagged_members
from ..instruments.instrument_manager import InstrumentManager
from .single_instr_panel import SingleInstrPanel

MODULE_PATH = os.path.dirname(__file__)

class MainPanelModel(PrefAtom):
    """
    """
    instr_manager = Typed(InstrumentManager, ())
    available_profiles = ContainerList(Unicode())
    used_profiles = Dict(Unicode())
    measure_profiles = List(Unicode())
    panels = List(Instance(PrefAtom))
    
    enable_dock_events = Bool(True)
    
    def __init__(self):
        super(MainPanelModel, self).__init__()
        
    def save_panel_state(self, dock_area):
        # here need to get all panels in terms of enaml widgets to extract from
        # them the model type and state but also the ui types
        # must also dump the layout
        pass
    
    def load_panel_state(self):
        # Here must build all the panels according to their types and then load
        # the layout
        # must disable dock events as each insertion and layout applying will 
        # generate a lot of them
        pass
    
    def drivers_request(self, profiles, target = 'measure'):
        """
        """
        used = self.used_profiles
        for profile in profiles:
            if profile in used:
                panel = used[profile]
                panel.release_driver()
                del used[profile]
        if target == 'measure':
            self.measure_profiles = profiles
#        elif isinstance(target, MacroPanel):
#            for profile in profiles:
#                used[profile] = target           
        
    def drivers_released(self, profiles, owner = 'measure'):
        """
        """
        if owner == 'measure':
            self.measure_profiles = []
            
        elif isinstance(owner, SingleInstrPanel):
            profile = profiles[0]
            del self.used_profiles[profile]
            self.available_profiles.append(profile)
            
#        elif isinstance(target, MacroPanel):
#            used = self.used_profiles
#            for profile in profiles:
#                panel = used[profile]
#                del used[profile]
#            self.available_profiles.extend(profiles)
    
    def control_panel_closed(self, panel_model):
        """
        """
        # Called by the view, and get the model of the closed panel
        if panel_model in self.used_profiles.items():
            self.drivers_released([panel_model.profile], owner = panel_model)
                
        self.panels.remove(panel_model)
    
    @observe('instr_manager.instrs')
    def _profiles_updated(self, change):
        """
        """
        instrs = change['value']
        used = set(self.used_profiles.keys() + self.measure_profile)
        self.available_profiles = [instrs[p] for p in instrs
                                    if instrs[p] not in used]   
                                    
    def _observe_available_profiles(self, change):
        """
        """
        if 'oldvalue' in change:
            new = list(set(change['value']) - set(change['oldvalue']))
        else:
            new = change['value']
            
        si_filter = lambda x : isinstance(x, SingleInstrPanel)
        inactive_si_panels = set(filter(si_filter, self.panels))- \
                            set(filter(si_filter, self.used_profiles.keys()))

        for profile in new:
            for si_panel in inactive_si_panels:
                if profile == si_panel.profile:
                    with self.suppress_notifications:
                        self.available_profiles.remove(profile)
                    si_panel.restart_driver()
                    self.used_profiles[profile] = si_panel
                    break
        #TODO update new and restart auto macro if possible