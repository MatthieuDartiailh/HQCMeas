# -*- coding: utf-8 -*-

from atom.api import Atom, List, Dict, Str, Callable, Bool, Enum

class DriverDebugPanel(Atom):
    
    driver_types
    driver_type

    drivers
    driver
    
    driver_properties
    driver_methods
    
    profiles
    profile

    connected
    driver_ready
    mode
    
    _driver_instance
        
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
        pass
    
    def attempt_set(self, prop, val):
        """
        """
        pass
    
    def attempt_call(self, meth):
        """
        """
        pass