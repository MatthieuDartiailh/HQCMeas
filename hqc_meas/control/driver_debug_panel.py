# -*- coding: utf-8 -*-

from atom.api import (Atom, List, Dict, Str, Callable, Bool, Unicode,
                      Instance, Typed, Value)
from inspect import getmembers, getabsfile, ismethod               
                      
from ..atom_util import Subclass
from ..instruments.drivers import BaseInstrument, DRIVERS, DRIVER_TYPES
from ..instruments.drivers.driver_tools import instrument_property
from ..instruments.instrument_form import InstrumentForm
from ..instrument.instrument_manager import matching_instr_list

class DriverDebugPanel(Atom):

    drivers = Dict(Str(), Subclass(BaseInstrument), DRIVERS)
    driver = Subclass(BaseInstrument)
    
    driver_properties = List(Str())
    driver_methods = List(Callable())
    
    profiles = Dict(Str(), Unicode())
    profile = Value()
    custom_form = Typed(InstrumentForm, kwargs = {'name' :'Debug'})

    connected = Bool()
    driver_ready = Bool()
    errors = Str()
    
    _driver_instance = Instance(BaseInstrument)
        
    def start_driver(self):
        """
        """
        pass
    
    def open_connection(self):
        """
        """
        pass
    
    def close_connection(self):
        """
        """
        pass
    
    def reopen_connetion(self):
        """
        """
        pass
    
    def reload_driver(self):
        """
        """
        pass
    
    def attempt_get(self, prop):
        """
        """
        try:
            val = getattr(self._driver_instance, prop)
            return val
        except Exception as e:
            return e
    
    def attempt_set(self, prop, val):
        """
        """
        try:
            setattr(self._driver_instance, prop, val)
            return True
        except Exception as e:
            return e
    
    def attempt_call(self, meth, args, kwargs):
        """
        """
        try:
            res = meth(self._driver_instance, *args, **kwargs)
            return res
        except Exception as e:
            return e
    
    def _observe_driver(self, change):
        """
        """
        driver = change['value']
        self.profiles = matching_instr_list(driver)
        
        # Updating the custom form
        for d_name, d_type in DRIVER_TYPES.iteritems():
            if issubclass(driver, d_type):
                self.custom_form.driver_type = d_name
                break
        for d_name, d in DRIVERS.iteritems():
            if d == driver:
                self.custom_form.driver = d_name
                break
        
        # Listing driver properties
        self.driver_properties = [m.__name__ for m in getmembers(driver,
                             lambda x : isinstance(x, instrument_property))]
        
        # Listing driver method
        self.driver_methods = [meth for meth in getmembers(driver, ismethod)
                                if meth.__name__ not in self.driver_properties
                                or meth.__name__.startswith('_')]
                                
    def _observe_profile(self, change):
        self.driver_ready = bool(change['value'])