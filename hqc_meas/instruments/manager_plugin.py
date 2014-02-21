# -*- coding: utf-8 -*-
#==============================================================================
# module : instrument_manager.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
import os
import logging
from importlib import import_module
from atom.api import (Callable, Str, Dict, List, Unicode, Typed, Subclass,
                      ContainerList)
from enaml.core.declarative import Declarative, d_

from watchdog.observers import Observer
from watchdog.events import (FileSystemEventHandler, FileCreatedEvent,
                             FileDeletedEvent, FileMovedEvent)
from inspect import cleandoc
from configobj import ConfigObj
from collections import defaultdict

from ..enaml_util.pref_plugin import HasPrefPlugin
from .drivers.driver_tools import BaseInstrument


class InstrUser(Declarative):
    """Extension to the 'instr_users' extensions point of the ManagerPlugin.

    Attributes
    ----------
    release_method: str
        Id of the command to call when the ManagerPlugin needs to get an
        instrument profile back from its current user. It will pass a list
        of profiles to release. It should return a bool indicating whether
        or not the operation succeeded. The released_profiles command must
        not be called by the release_method.

    default_policy:
        Does by default the user allows the manager to get the profile back
        when needed.

    """
    release_method = d_(Callable())

    default_policy = d_(Str('releasable'))


USERS_POINT = u'hqc_meas.instr_manager.users'

MODULE_PATH = os.path.dirname(__file__)



def open_profile(profile_path):
    """ Access the profile specified

    Parameters
    ----------
    profile_path : unicode
        Path to the file in which the profile is stored

    """
    return ConfigObj(profile_path).dict()


def save_profile(profile_path, profile_infos):
    """ Save a profile to a file

    Parameters
    ----------
    profile_path : unicode
        Path of the file to which the profile should be saved

    profiles_infos : dict
        Dict containing the profiles infos
    """
    conf = ConfigObj()
    conf.update(profile_infos)
    conf.write(profile_path)


class InstrManagerPlugin(HasPrefPlugin):
    """
    """

    profiles_folders = List(Unicode(),
                            [(os.path.join(MODULE_PATH,
                                           'profiles'))]).tag(pref=True)

    # Drivers loading exception
    drivers_loading = List(Unicode()).tag(pref=True)

    drivers_type = List()

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
        super(InstrManagerPlugin, self).start()
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

    def driver_types_request(self, driver_types):
        """ Give access to the driver type implementation

        Parameters
        ----------
        driver_types : list(str)
            The names of the driver types the user want to get the classes.

        Returns
        -------
        driver_types : dict
            The required driver types as a dict {name: class}
        """
        return {key: val for key, val in self._drivers_types.iteritems()
                if key in driver_types}

    def drivers_request(self, drivers):
        """ Give access to the driver type implementation

        Parameters
        ----------
        drivers : list(str)
            The names of the drivers the user want to get the classes.

        Returns
        -------
        drivers : dict
            The required drivers as a dict {name: class}
        """
        return {key: val for key, val in self._drivers.iteritems()
                if key in drivers}

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
        profiles : dict
            The required profiles as a dict {name: profile}
        """
        to_release = defaultdict(list)
        # Identify the profiles which need to be released
        for prof in profiles:
            if prof in self._used_profiles:
                old_owner = self._used_profiles[prof]
                decl = self._users[old_owner]
                if decl.default_policy == 'unreleasable':
                    return False, {}

                to_release[decl.release_method].append(prof)

        if to_release:
            core = workbench.get_plugin('enaml.workbench.core')
            for meth, profs in to_release.iteritems():
                res = core.invoke_command(meth, {'profiles': profs}, self)
                if not res:
                    return False, {}

        # Now that we are sure that the profiles can be sent to the users,
        # remove them from the available_profiles list register who is using
        # them,  and load them
        avail = self.available_profiles
        self.available_profiles = [prof for prof in avail
                                   if prof in profiles]

        used = {prof: new_owner for prof in profiles}
        self._used_profiles.update(used)

        mapping = self._profiles_map
        profile_objects = {prof: load_profile(mapping[prof])
                           for prof in profiles}

        return True, profile_objects

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
        mapping = self._used_profiles
        for prof in profiles:
            del mapping[prof]

        avail = list(self.available_profiles)
        self.available_profiles = avail + profiles

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
        profiles_dict = {}
        for driver in drivers:
            profs = {prof for prof, path in self._profiles_map.iteritems()
                     if open_profile(path)['driver'] == driver}:
            profiles_dict.update(profs)

        return profile_dict

    #--- Private API ----------------------------------------------------------
    # Drivers types
    _driver_types = Dict(Str(), Subclass(BaseInstrument))

    # Drivers
    _drivers = Dict(Str(), Subclass(BaseInstrument))

    # Mapping between profile names and path to .ini file holding the data.
    _profiles_map = Dict(Str(), Unicode())

    # Mapping between profile names and user id.
    _used_profiles = Dict(Str(), Tuple())

    # Mapping between plugin_id and InstrUser declaration.
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
        """ Refresh the known driver types and drivers.

        """
        path = os.path.join(MODULE_PATH, 'drivers')
        modules = sorted(m[:-3] for m in os.listdir(path)
                         if (os.path.isfile(os.path.join(path, m))
                             and m.endswith('.py')))
        modules.remove('__init__')
        modules.remove('driver_tools')
        for mod in modules[:]:
            if mod in self.driver_loading:
                modules.remove(mod)

        driver_types = {}
        driver_packages = []
        drivers = {}
        failed = {}
        self._explore_modules(modules, driver_types, driver_packages, drivers,
                              failed)

        # Remove packages which should not be explored
        for pack in driver_packages[:]:
            if pack in self.driver_loading:
                driver_packages.remove(pack)

        # Explore packages
        while driver_packages:
            pack = driver_packages.pop(0)
            pack_path = os.path.join(path, os.path.join(pack.split('.'))
            if not os.path.isdir(pack_path):
                log = logging.getLogger(__name__)
                mess = '{} is not a valid directory.({})'.format(pack,
                                                                 pack_path)
                log.error(mess)
                failed[pack] = mess
                continue

            modules = sorted(rel + '.' + m[:-3] for m in os.listdir(pack_path)
                             if (os.path.isfile(os.path.join(path, m))
                                 and m.endswith('.py')))
            try:
                modules.removes(rel + '__init__')
            except ValueError:
                log = logging.getLogger(__name__)
                mess = cleandoc('''{} is not a valid Python package (miss
                    __init__.py).'''.format(pack))
                log.error(mess)
                failed[pack] = mess
                continue

            # Remove modules which shouldnjot be imported
            for mod in modules[:]:
                if mod in self.driver_loading:
                    modules.remove(mod)

            self._explore_modules(modules, driver_types, driver_packages,
                                  drivers, failed, prefix=pack)

            # Remove packages which should not be explored
            for pack in driver_packages[:]:
                if pack in self.driver_loading:
                    driver_packages.remove(pack)

        self._drivers = drivers
        self._drivers_types = driver_types

        # TODO do something with failed

    @staticmethod
    def _explore_modules(modules, types, packages, drivers, failed,
                         prefix=None):
        """ Explore a list of modules.

        Parameters
        ----------
        modules : list
            The list of modules of explore

        types : dict
            A dict in which discovered types will be stored.

        packages : list
            A list in which discovered packages will be stored.

        drivers : dict
            A dict in which discovered drivers will be stored.

        failed : list
            A list in which failed imports will be stored.
        """
        for mod in modules:
            try:
                m = import_module('.drivers.' + mod)
            except Exception as e:
                log = logging.getLogger(__name__)
                mess = 'Failed to import {} : {}'.format(mod, e.message)
                log.error(mess)
                failed[mod] = mess
                continue

            if hasattr(m, 'DRIVER_TYPES'):
                types.update(m.DRIVERS_TYPES)

            if hasattr(m, 'DRIVER_PACKAGES'):
                if prefix is not None:
                    packs = [prefix + '.' + pack for pack in m.DRIVER_PACKAGES]
                else:
                    packs = m.DRIVER_PACKAGES
                packages.extend(packs)

            if hasattr(m, 'DRIVERS'):
                drivers.update(m.DRIVERS)

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

        Parameters
        ----------
        extension : Extension
            The extension object of interest

        Returns
        -------
        user : User
            The first InstrUser object declared by the extension
        """
        workbench = self.workbench
        users = extension.get_children(InstrUser)
        if extension.factory is not None and not users:
            user = extension.factory(workbench)
            if not isinstance(user, InstrUser):
                msg = "extension '%s' created non-State of type '%s'"
                args = (extension.qualified_id, type(user).__name__)
                raise TypeError(msg % args)
        else:
            user = users[0]

        return user

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

        for folder in self.profiles_folder:
            handler = _FileListUpdater(self._refresh_profiles_map)
            self._observer.schedule(handler, folder, recursive=True)

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
    """Simple watchdog handler used for auto-updating the profiles list

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
