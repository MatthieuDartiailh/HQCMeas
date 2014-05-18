# -*- coding: utf-8 -*-
#==============================================================================
# module : driver_debugger.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import (List, Str, Callable, Bool, Instance, Value, Tuple)
from inspect import getmembers, ismethod

from hqc_meas.instruments.drivers.driver_tools\
    import BaseInstrument, instrument_property

from ..debugger import BaseDebugger


class DriverDebugger(BaseDebugger):
    """
    """

    #--- Members --------------------------------------------------------------

    #: State object describing the current state of the instrument manager.
    instr_manager_state = Value()

    # TODO currently unused , add filtering in UI
    #: List of known drivers.
    drivers = List(Str())

    #: Currently selected driver.
    driver = Str()

    #: Instance of the driver being tested.
    driver_instance = Instance(BaseInstrument)

    #: Attributes of the driver being tested.
    driver_attributes = List(Str())

    #: Properties of the driver being tested.
    driver_properties = List(Str())

    #: Methods of the driver being tested (no getter/setter)
    driver_methods = List(Callable())

    #: List of profiles matching the currently selected driver.
    profiles = List(Str())

    #: Name of the currently selected profile or dict if a custom form is used.
    profile = Value()

    #: Form corresponding to the type of driver currently selected, both the
    #: form and its associated vview are stored.
    custom_form = Tuple(default=(None, None))

    #: Is an active connection opened.
    connected = Bool()

    #: Can we open a connection with the information we have.
    driver_ready = Bool()

    #: Simple error message recording.
    errors = Str()

    #--- Puclic methods -------------------------------------------------------

    def __init__(self, **kwargs):
        super(DriverDebugger, self).__init__(**kwargs)
        self.instr_manager_state.observe('all_profiles',
                                         self._refresh_profiles)

    def release_ressources(self):
        if self.connected:
            self.close_driver()
        self.instr_manager_state.unobserve('all_profiles',
                                           self._refresh_profiles)

    def start_driver(self):
        """ Start the selected driver with the selected profile.

        """
        # If profile is a dict the user is using a custom form so no request
        # need to be performed.
        core = self.plugin.workbench.get_plugin('enaml.workbench.core')
        if not isinstance(self.profile, dict):
            cmd = 'hqc_meas.instr_manager.profiles_request'
            profs, _ = core.invoke_command(cmd, {'profiles': [self.profile]},
                                           self.plugin)
            if not profs:
                mes = 'Instr manager could not release the profile' + '\n'
                self.errors += mes
                return

            profile_dict = profs[self.profile]
        else:
            profile_dict = self.profile

        cmd = 'hqc_meas.instr_manager.drivers_request'
        drivers, _ = core.invoke_command(cmd, {'drivers': [self.driver]},
                                         self)

        try:
            driver = drivers[self.driver]
            driver_instance = driver(profile_dict)
            # Listing drivers attributes
            parent = [m[0] for m in getmembers(driver)]
            self.driver_attributes = [m for m in dir(driver_instance)
                                      if m not in parent
                                      and not m.startswith('_')]
            self.driver_instance = driver_instance
            self.connected = True
        except Exception as e:
            self.errors += e.message + '\n'
            self.driver_instance = None
            if not isinstance(self.profile, dict):
                cmd = 'hqc_meas.instr_manager.profiles_released'
                core.invoke_command(cmd, {'profiles': [self.profile]},
                                    self.plugin)

    def open_connection(self):
        """ Open the connection to an instrument.

        """
        try:
            self.driver_instance.open_connection()
            self.connected = True
        except Exception as e:
            self.errors += e.message + '\n'

    def close_connection(self):
        """ Close the connection to the instrument.

        This method does not release the instrument profile.

        """
        try:
            self.driver_instance.close_connection()
            self.connected = False
        except Exception as e:
            self.errors += e.message + '\n'

    def reopen_connection(self):
        """ Close and reopen the connection to an instrument.

        """
        try:
            self.driver_instance.reopen_connection()
        except Exception as e:
            self.connected = False
            self.errors += e.message + '\n'

    def reload_driver(self):
        """
        """
        core = self.plugin.workbench.get_plugin('enaml.workbench.core')
        cmd = 'hqc_meas.instr_manager.reload_driver'
        try:
            core.invoke_command(cmd, {'driver': self.driver}, self)
        except Exception as e:
            self.errors += 'Failed to reload driver {}: {}'.format(self.driver,
                                                                   e.message)

    def close_driver(self):
        """ Destroy the driver and release the instrument profile.

        """
        try:
            self.driver_instance.close_connection()
        except Exception as e:
            self.errors += e.message + '\n'

        self.connected = False
        self.driver_instance = None
        if not isinstance(self.profile, dict):
            core = self.plugin.workbench.get_plugin('enaml.workbench.core')
            core.invoke_command('hqc_meas.instr_manager.profiles_released',
                                {'profiles': [self.profile]}, self.plugin)

    def attempt_get(self, prop):
        """ Try to get an instrument property value.

        Parameters
        ----------
        prop : str
            Name of the instrument property to get.

        Returns
        -------
        val :
            Value of the instrument property or erroir raised by the getter.

        """
        try:
            val = getattr(self.driver_instance, prop)
            return val
        except Exception as e:
            return e

    def attempt_set(self, prop, val):
        """ Try to set an instrument property.

        Parameters
        ----------
        prop : str
            Name of the instrument property to set.

        val : str
            Value to which the instrument property should be set. This value is
            first evaluated before being sent.

        Returns
        -------
        result : bool or Exception
             True if the command succeeded or the error if one was raised by
             the setter.

        """
        try:
            aux = eval(val)
            setattr(self.driver_instance, prop, aux)
            return True
        except Exception as e:
            return e

    def attempt_call(self, meth, args, kwargs):
        """ Try to call a driver method.

        """
        try:
            res = meth(self.driver_instance, *args, **kwargs)
            return res
        except Exception as e:
            return e

    #--- Private API ----------------------------------------------------------

    def _refresh_profiles(self, change):
        """ Refresh the list of matching profiles for the selected driver.

        """
        if self.driver:
            core = self.plugin.workbench.get_plugin('enaml.workbench.core')
            cmd = 'hqc_meas.instr_manager.matching_profiles'
            self.profiles = core.invoke_command(cmd,
                                                {'drivers': [self.driver]},
                                                self)

    def _observe_driver(self, change):
        """
        """
        core = self.plugin.workbench.get_plugin('enaml.workbench.core')
        cmd = 'hqc_meas.instr_manager.drivers_request'
        drivers, _ = core.invoke_command(cmd, {'drivers': [change['value']]},
                                         self)
        driver = drivers.get(change['value'])
        if not driver:
            return

        self.driver_instance = None
        self._refresh_profiles({})

        cmd = 'hqc_meas.instr_manager.matching_form'
        form = core.invoke_command(cmd, {'driver': self.driver, 'view': True},
                                   self)
        if form:
            self.custom_form = (form[0](), form[1])
        else:
            self.custom_form = (None, None)

        # Listing driver properties
        self.driver_properties = [m[0] for m in getmembers(driver,
                                  lambda x: isinstance(x,
                                                       instrument_property))]

        parent = set([m[0] for m in getmembers(object)])
        parent.update(set(['open_connection', 'close_connection',
                          'reopen_connection']))
        parent.update(set([m[0] for m in
                           getmembers(driver, lambda x: isinstance(x,
                                                                   property))]
                          ))
        # Listing driver method
        self.driver_methods = [meth[1] for meth in getmembers(driver, ismethod)
                               if meth[0] not in self.driver_properties
                               and not meth[0].startswith('_')
                               and meth[0] not in parent]

    def _observe_profile(self, change):
        self.driver_ready = bool(change['value'] is not None)

    def _default_instr_manager_state(self):
        core = self.plugin.workbench.get_plugin('enaml.workbench.core')
        state_id = 'hqc_meas.states.instr_manager'
        state = core.invoke_command('hqc_meas.state.get',
                                    {'state_id': state_id})
        return state
