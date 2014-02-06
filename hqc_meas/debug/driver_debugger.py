# -*- coding: utf-8 -*-

from atom.api import (Atom, List, Dict, Str, Callable, Bool, Unicode,
                      Instance, Value)
from inspect import getmembers, ismethod
from configobj import ConfigObj

from ..atom_util import Subclass
from ..instruments.drivers import BaseInstrument, DRIVERS, DRIVER_TYPES
from ..instruments.drivers.driver_tools import instrument_property
from ..instruments.forms import AbstractConnectionForm, FORMS
from ..instruments.instrument_manager import matching_instr_list


class DriverDebugger(Atom):
    """
    """

    drivers = Dict(Str(), Subclass(BaseInstrument), DRIVERS)
    driver = Subclass(BaseInstrument)

    driver_attributes = List(Str())
    driver_properties = List(Str())
    driver_methods = List(Callable())

    profiles = Dict(Str(), Unicode())
    profile = Value()
    custom_form = Instance(AbstractConnectionForm)

    connected = Bool()
    driver_ready = Bool()
    errors = Str()

    driver_instance = Instance(BaseInstrument)

    def start_driver(self):
        """
        """
        prof = self.profile
        if not isinstance(prof, dict):
            prof = ConfigObj(prof).dict()
        try:
            driver_instance = self.driver(prof)
            # Listing drivers attributes
            parent = [m[0] for m in getmembers(self.driver)]
            self.driver_attributes = [m for m in getmembers(driver_instance)
                                      if m[0] not in parent]
            self.driver_instance = driver_instance
            self.connected = True
        except Exception as e:
            self.errors += e.message + '\n'

    def open_connection(self):
        """
        """
        try:
            self.driver_instance.open_connection()
            self.connected = True
        except Exception as e:
            self.errors += e.message + '\n'

    def close_connection(self):
        """
        """
        try:
            self.driver_instance.close_connection()
            self.connected = False
        except Exception as e:
            self.errors += e.message + '\n'

    def reopen_connetion(self):
        """
        """
        try:
            self.driver_instance.reopen_connection()
            self.connected = False
        except Exception as e:
            self.errors += e.message + '\n'

    def reload_driver(self):
        """
        """
        pass

    def attempt_get(self, prop):
        """
        """
        try:
            val = getattr(self.driver_instance, prop)
            return val
        except Exception as e:
            return e

    def attempt_set(self, prop, val):
        """
        """
        try:
            setattr(self.driver_instance, prop, val)
            return True
        except Exception as e:
            return e

    def attempt_call(self, meth, args, kwargs):
        """
        """
        try:
            res = meth(self.driver_instance, *args, **kwargs)
            return res
        except Exception as e:
            return e

    def _observe_driver(self, change):
        """
        """
        driver = change['value']
        self.driver_instance = None
        self.profiles = matching_instr_list(driver)

        # Updating the custom form
        for d_name, d_type in DRIVER_TYPES.iteritems():
            if issubclass(driver, d_type):
                self.custom_form = FORMS[d_name]
                break

        # Listing driver properties
        self.driver_properties = [m.__name__ for m in getmembers(driver,
                                  lambda x: isinstance(x,
                                                       instrument_property))]

        # Listing driver method
        self.driver_methods = [meth for meth in getmembers(driver, ismethod)
                               if meth.__name__ not in self.driver_properties
                               or meth.__name__.startswith('_')]

    def _observe_profile(self, change):
        self.driver_ready = bool(change['value'])
