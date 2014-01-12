# -*- coding: utf-8 -*-
from atom.api import (Atom, Unicode, Bool, Typed, Dict, observe, Str, List)
from enaml.core.enamldef_meta import EnamlDefMeta
from enaml.widgets.api import DockArea
from enaml.layout.api import InsertItem
import enaml

from ..single_instr_panel import SingleInstrPanel
from ..main_panel import MainPanelModel
from ...instruments.drivers import BaseInstrument, DRIVERS
from ...atom_util import Subclass
from ...instruments.instrument_manager import matching_instr_list

from ..panels import SINGLE_INSTR_PANELS
from ..panels.views import SINGLE_INSTR_VIEWS
from .pref_building import SingleInstrPref, PREF_MAPPING

with enaml.imports():
    from ..single_instr_view import SingleInstrDock

def build_single_instr_panel(panel_class, state, main_ui, second_ui, prop_ui,
                main_panel, area):
    """
    """
    profile = state['pref']['profile']
    if state['profile_available']:
        with main_panel.suppress_notifications:
            main_panel.available_profiles.remove(profile)
    model = panel_class(state = state)
    main_panel.used_profiles[profile] = model
    
    dock_numbers = sorted([pane.name[5] for pane in area.dock_items()])
    if dock_numbers and dock_numbers[-1] > len(dock_numbers):
        first_free = min(set(xrange(len(dock_numbers))) - dock_numbers)
        name = 'item_{}'.format(first_free)
    else:
        name = 'item_{}'.format(len(dock_numbers) + 1)
        
    SingleInstrDock(area, model = model, name = name,
                    main_ui = main_ui, second_ui = second_ui,
                    prop_ui = prop_ui)
    area.update_layout(InsertItem(item = name))
    
class SingleInstrBuilder(Atom):
    """
    """
    main_panel = Typed(MainPanelModel)
    area = Typed(DockArea)    
    
    driver_map = Dict(Str(), Subclass(BaseInstrument))
    driver_key = Str()
    driver_type = Subclass(BaseInstrument)
    model_type = Subclass(SingleInstrPanel)
    
    profile_map = Dict(Str(), Unicode())
    profile = Unicode()
    
    available_uis = Dict(Str(), List(Typed(EnamlDefMeta)),
                         {'main' : [], 'aux' : [], 'prop' : []})
    main_ui = Typed(EnamlDefMeta)
    second_ui = Typed(EnamlDefMeta)
    prop_ui = Typed(EnamlDefMeta)
    
    pref_model = Typed(SingleInstrPref)
    
    ready_to_build = Bool()
    
    def build_panel(self):
        """
        """
        profile_available = self.profile in self.main_panel.available_profiles
                
        state = {'pref' : {'profile' : self.profile},
                'profile_available' : profile_available}
        state['pref'].update(self.pref_model.preferences)
        
        build_single_instr_panel(self.model_type, state, 
                                 self.main_ui, self.second_ui, self.prop_ui,
                                 self.main_panel, self.area)       
    
    @observe('profile', 'main_ui', 'pref_model.title')
    def _is_ready_to_build(self, change):
        """
        """
        if self.pref_model:
            self.ready_to_build = bool(self.driver_type and self.model_type
                                    and self.profile != u'' and self.main_ui
                                    and self.pref_model.title != '')
    
    def _observe_driver_key(self, change):
        """
        """
        key  = change['value']
        if key:
            self.driver_type = self.driver_map[key]
            model_type = SINGLE_INSTR_PANELS[key][0]
            self.model_type = model_type
            self.profile_map = matching_instr_list(key)
            
            uis = SINGLE_INSTR_VIEWS[model_type]
            uis['prop'] = uis['aux'] + uis['prop']
            self.available_uis = uis
            for m_class in type.mro(model_type):
                if m_class in PREF_MAPPING:
                    self.pref_model = PREF_MAPPING[m_class](model_type)
                    break
                
    def _observe_second_ui(self, change):
        """
        """
        self.prop_ui = change['value']
    
    def _default_driver_map(self):
        """
        """
        return {key : val for key, val in DRIVERS.iteritems()
                if key in SINGLE_INSTR_PANELS}