# -*- coding: utf-8 -*-
#==============================================================================
# module : instrument_manager.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
import os
from atom.api import Callable, Str, Dict, List, Unicode, Typed
from enaml.core.declarative import Declarative, d_

from watchdog.observers import Observer
from watchdog.events import (FileSystemEventHandler, FileCreatedEvent,
                             FileDeletedEvent, FileMovedEvent)

from ..enaml_util.pref_plugin import HasPrefPlugin


class InstrUser(Declarative):
    """Extension to the 'instr_users' extensions point of the ManagerPlugin.

    Attributes
    ----------
    release_method: callable
        Callable to use when the ManagerPlugin needs to get a instrument
        profile back from its current user.

    default_policy:
        Does by default the user allows the manager to get the profile back
        when needed.

    """
    release_method = d_(Callable())

    default_policy = d_(Str())


USERS_POINT = u'hqc_meas.instr_manager.users'

MODULE_PATH = os.path.dirname(__file__)


class InstrManagerPlugin(HasPrefPlugin):
    """
    """

    profiles_folders = List(Unicode(),
                            [(os.path.join(MODULE_PATH,
                                           'profiles'))]).tag(pref=True)

    # Drivers loading exception
    drivers_loading = List(Unicode()).tag(pref=True)

    #Name: class
    drivers = List()

    #Name: path
    all_profiles = List()

    #Name: path
    available_profiles = List()

    def start(self):
        """ Start the plugin life-cycle.

        This method is called by the framework at the appropriate time.
        It should never be called by user code.

        """
        # TODO get preferences
        self._refresh_users()
        self._bind_observers()

    def stop(self):
        """ Stop the plugin life-cycle.

        This method is called by the framework at the appropriate time.
        It should never be called by user code.

        """
        self._unbind_observers()
        self._users.clear()
        # TODO clear all ressources, save preferences

    def profiles_request(self, new_owner, profiles):
        """ Register the user of the specified profiles.

        If necessary this method will try to free profiles used by different
        owners, however it might fail in doing so and the client must be able
        to handle.

        Parameters
        ----------
        new_owner : Plugin
            The object requesting the right to use some profiles

        profiles : list(str)
            The names of the profiles the user want the privilege to use.

        Returns
        -------
            result : bool
                Whether or not the manager grant the user the privilege to use
                the profiles.
            profiles : list(dict)
                The required profiles as dict
        """
        pass

    def profiles_released(self, owner, profiles):
        """ Notify the manager that the specified are not used anymore

        The user should not keep any reference to the profile after this call.

        Parameters
        ----------
        owner : Plugin
            Current owner of the profiles

        profiles : list(str)
            The names of the profiles the user is not using anymore.

        """
        pass

    def matching_profiles(self, drivers):
        """ List the existing profile whose driver is in the specified list

        Parameters
        ----------
        drivers : list(str)
            Names of the driver for which matching profiles should be returned

        Returns
        -------
        profiles : list(str)
            Names of the matching profiles
        """
        pass

    #--- Private API ----------------------------------------------------------

    # Mapping between profile names and path to .ini file holding the data
    _profiles_map = Dict(Str(), Unicode())

    # Mapping between profile names and user object
    _used_profiles = Dict(Str())

    # Mapping between plugin_id and InstrUser declaration
    _users = Dict(Str(), Typed(InstrUser))

    # Watchdog observer
    _observer = Typed(Observer, ())

    def _refresh_profiles_map(self):
        """ Refresh the known profiles

        """
        profiles = {}
        for path in self.profiles_folders:
            filenames = sorted(f for f in os.listdir(path)
                               if (os.path.isfile(os.path.join(path, f))
                                   and f.endswith('.ini')))

            for filename in filenames:
                profile_name = self._normalise_name(filename)
                prof_path = os.path.join(self.instr_folder, filename)
                # Beware redundant names are overwrited
                profiles[profile_name] = prof_path

        self._profiles_map = profiles
        self.all_profiles = list(profiles.keys())
        self.available_profiles = [profile for profile in profiles.keys()
                                   if profile not in self._used_profiles]

    def _refresh_drivers(self):
        """ Refresh the known drivers.

        """
        pass
        # must be very careful when importing to give the user a chance to
        # change the preferences

    def _refresh_users(self):
        """ Refresh the list of potential users.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(USERS_POINT)
        extensions = point.extensions
        if not extensions:
            self._users.clear()
            return

        new_users = {}
        old_users = self._users
        for extension in extensions:
            plugin_id = extension.plugin_id
            if plugin_id in old_users:
                user = old_users[plugin_id]
            else:
                user = self._load_user(plugin_id)
            new_users[plugin_id] = user

        self._users = new_users

    def _load_user(self, extension):
        """ Load the user object for the gicen extension.

        """
        pass

    def _on_users_updated(self, change):
        """ The observer for the commands extension point.

        """
        self._refresh_users()

    def _bind_observers(self):
        """ Setup the observers for the plugin.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(USERS_POINT)
        point.observe('extensions', self._on_users_updated)

        self._observer.schedule(_FileListUpdater(self._refresh_profiles_map),
                                self.profiles_folder, recursive=True)

    def _unbind_observers(self):
        """ Remove the observers for the plugin.

        """
        self._observer.unchedule_all()

        workbench = self.workbench
        point = workbench.get_extension_point(USERS_POINT)
        point.unobserve('extensions', self._on_users_updated)

    @staticmethod
    def _normalise_name(name):
        """Normalize the name of the profiles by replacing '_' by spaces,
        removing the extension, and adding spaces between 'aA' sequences.
        """
        if name.endswith('.ini') or name.endswith('Task'):
            name = name[:-4] + '\0'
        aux = ''
        for i, char in enumerate(name):
            if char == '_':
                aux += ' '
                continue

            if char != '\0':
                if char.isupper() and i != 0:
                    if name[i-1].islower():
                        if name[i+1].islower():
                            aux += ' ' + char.lower()
                        else:
                            aux += ' ' + char
                    else:
                        if name[i+1].islower():
                            aux += ' ' + char.lower()
                        else:
                            aux += char
                else:
                    if i == 0:
                        aux += char.upper()
                    else:
                        aux += char
        return aux


class _FileListUpdater(FileSystemEventHandler):
    """Simple `watchdog` handler used for auto-updating the profiles list
    """
    def __init__(self, handler):
        self.handler = handler

    def on_created(self, event):
        super(_FileListUpdater, self).on_created(event)
        if isinstance(event, FileCreatedEvent):
            self.handler()

    def on_deleted(self, event):
        super(_FileListUpdater, self).on_deleted(event)
        if isinstance(event, FileDeletedEvent):
            self.handler()

    def on_moved(self, event):
        super(_FileListUpdater, self).on_deleted(event)
        if isinstance(event, FileMovedEvent):
            self.handler()
