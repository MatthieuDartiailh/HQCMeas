# -*- coding: utf-8 -*-

from atom.api import (Atom, List, Dict, Str, Callable, Bool, Unicode,
                      Instance, Value)
from inspect import getmembers, ismethod, getmodule, isclass
from configobj import ConfigObj

from ..atom_util import Subclass
from ..instruments.drivers import BaseInstrument, DRIVERS, DRIVER_TYPES
from ..instruments.drivers.driver_tools import instrument_property
from ..instruments.forms import AbstractConnectionForm, FORMS
from ..instruments.instrument_manager import matching_instr_list

# TODO turn this into, a plugin using InstrManager.


class DriverDebugger(Atom):
    """
    """

    #--- Members --------------------------------------------------------------

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

    #--- Puclic methods -------------------------------------------------------

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
            self.driver_attributes = [m[0] for m in getmembers(driver_instance)
                                      if m[0] not in parent
                                      and not m[0].startswith('_')]
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

    def reopen_connection(self):
        """
        """
        try:
            self.driver_instance.reopen_connection()
        except Exception as e:
            self.connected = False
            self.errors += e.message + '\n'

    def reload_driver(self):
        """
        """
        try:
            mod = getmodule(self.driver)
            mod = reload(mod)
            mem = getmembers(mod, isclass)
            name = self.driver.__name__

            with self.suppress_notifications():
                self.driver = [m[1] for m in mem if m[0] == name][0]

            self.driver_instance = None

            for i, driver in enumerate(DRIVERS.values()):
                if driver.__name__ == self.driver.__name__:
                    DRIVERS[i] = self.driver

        except TypeError:
            self.errors += 'Failed to reload driver\n'

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
            aux = eval(val)
            setattr(self.driver_instance, prop, aux)
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

    #--- Observers ------------------------------------------------------------

    def _observe_driver(self, change):
        """
        """
        driver = change['value']
        if driver is None:
            return

        driver_id = [k for k, v in self.drivers.iteritems()
                     if v == driver][0]
        self.driver_instance = None
        self.profiles = matching_instr_list(driver_id)

        # Updating the custom form
        for d_name, d_type in DRIVER_TYPES.iteritems():
            if issubclass(driver, d_type):
                self.custom_form = FORMS[d_name]()
                break

        # Listing driver properties
        self.driver_properties = [m[0] for m in getmembers(driver,
                                  lambda x: isinstance(x,
                                                       instrument_property))]

        parent = set([m[0] for m in getmembers(self.driver)])
        # Listing driver method
        self.driver_methods = [meth[1] for meth in getmembers(driver, ismethod)
                               if meth[0] not in self.driver_properties
                               and not meth[0].startswith('_')
                               and meth[0] not in parent]
        self.driver_methods.append(driver.check_instrument_cache)
        self.driver_methods.append(driver.clear_instrument_cache)

    def _observe_profile(self, change):
        self.driver_ready = bool(change['value'] is not None)
