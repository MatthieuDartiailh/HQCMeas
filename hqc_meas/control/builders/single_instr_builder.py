# -*- coding: utf-8 -*-
from atom.api import (Atom, Unicode, Bool, Typed, Dict, observe, Str, List)
from enaml.core.enamldef_meta import EnamlDefMeta
from enaml.widgets.api import DockArea
import enaml

from ..single_instr_panel import SingleInstrPanel
from ..main_panel import MainPanelModel
from ...instruments.drivers import BaseInstr, DRIVERS
from ...atom_util import Subclass
from ...instruments.instr_manager import matching_instr_list

from ..panels import SINGLE_INSTR_PANELS
from ..panels.views import SINGLE_INSTR_VIEWS
from .pref_building import SingleInstrPref, PREF_MAPPING

with enaml.imports():
    from ..single_instr_view import SingleInstrDock

class SingleInstrBuilder(Atom):
    """
    """
    main_panel = Typed(MainPanelModel)
    area = Typed(DockArea)    
    
    driver_map = Dict(Str(), Subclass(BaseInstr))
    driver_type = Subclass(BaseInstr)
    model_type = Subclass(SingleInstrPanel)
    
    profile_map = Dict(Str(), Unicode())
    profile = Unicode()
    
    available_uis = Dict(Str(), List(Typed(EnamlDefMeta)))
    main_ui = Typed(EnamlDefMeta)
    second_ui = Typed(EnamlDefMeta)
    prop_ui = Typed(EnamlDefMeta)
    
    pref_model = Typed(SingleInstrPref)
    
    ready_to_build = Bool()
    
    def build_panel(self):
        """
        """
        profile_available = self.profile in self.main_panel.available_profiles
        if profile_available:
            with self.suppress_notifications:
                self.main_panel.available_profiles.remove(self.profile)
                
        pref = {'pref' : {'profile' : self.profile},
                'profile_available' : profile_available}
        pref['pref'].update(self.pref_model.preferences)
        
        model = self.model_type(pref = pref)
        self.main_panel.used_profiles[self.profile] = model
        
        dock_numbers = sorted([pane.name[5] for pane in self.area.children])
        if dock_numbers[-1] > len(dock_numbers):
            first_free = min(set(xrange(len(dock_numbers))) - dock_numbers)
            name = 'item_{}'.format(first_free)
        else:
            name = 'item_{}'.format(len(dock_numbers) + 1)
            
        SingleInstrDock(model = model, name = name, area = self.area,
                        main_ui = self.main_ui, second_ui = self.second_ui,
                        prop_ui = self.prop_ui)
    
    @observe('profile', 'main_ui', 'pref_model.title')
    def _is_ready_to_build(self, change):
        """
        """
        if self.pref_model:
            self.ready_to_build = bool(self.driver_type and self.model_type
                                    and self.profile != u'' and self.main_ui
                                    and self.pref_model.title != '')
    
    def _observe_driver_type(self, change):
        """
        """
        driver_type = change['value']
        model_type = SINGLE_INSTR_PANELS[driver_type]
        self.model_type = model_type
        self.profile_map = matching_instr_list(driver_type)
        uis = {}
        uis['main'] = SINGLE_INSTR_VIEWS['main'][model_type]
        uis['aux'] = SINGLE_INSTR_VIEWS['aux'][model_type]
        uis['prop'] = uis['aux'] + SINGLE_INSTR_VIEWS['prop'][model_type]
        self.available_uis = uis
        for m_class in type.mro(model_type):
            if m_class in PREF_MAPPING:
                self.pref_model = PREF_MAPPING[m_class]()
                break
                
    def _observe_second_ui(self, change):
        """
        """
        self.prop_ui = change['value']
    
    def _default_driver_model_map(self):
        """
        """
        return {key : val for key, val in DRIVERS.iteritems()
                if val in SINGLE_INSTR_PANELS}