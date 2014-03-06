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
from atom.api import (Str, Dict, List, Unicode, Typed, Subclass, Tuple)

from watchdog.observers import Observer
from watchdog.events import (FileSystemEventHandler, FileCreatedEvent,
                             FileDeletedEvent, FileMovedEvent)
from inspect import cleandoc
from configobj import ConfigObj
from collections import defaultdict

from ..utils.has_pref_plugin import HasPrefPlugin
from .drivers.driver_tools import BaseInstrument
from .instr_user import InstrUser


USERS_POINT = u'hqc_meas.instr_manager.users'

MODULE_PATH = os.path.dirname(__file__)

MODULE_ANCHOR = 'hqc_meas.instruments'


def open_profile(profile_path):
    """ Access the profile specified

    Parameters
    ----------
    profile_path : unicode
        Path to the file in which the profile is stored

    """
    return ConfigObj(profile_path).dict()


def save_profile(directory, profile_name, profile_infos):
    """ Save a profile to a file

    Parameters
    ----------
    profile_path : unicode
        Path of the file to which the profile should be saved

    profiles_infos : dict
        Dict containing the profiles infos
    """
    path = os.path.join(directory, profile_name + '.ini')
    conf = ConfigObj()
    conf.update(profile_infos)
    conf.write(path)


class InstrManagerPlugin(HasPrefPlugin):
    """
    """
    # Directories in which the profiles are looked for.
    profiles_folders = List(Unicode(),
                            [os.path.join(MODULE_PATH,
                                          'profiles')]).tag(pref=True)

    # Drivers loading exception
    drivers_loading = List(Unicode()).tag(pref=True)

    # Name of the known driver types.
    driver_types = List()

    # Name of the known drivers.
    drivers = List()

    # Name of the known profiles.
    all_profiles = List()

    # Name of the currently available profiles.
    available_profiles = List()

    def start(self):
        """ Start the plugin life-cycle.

        This method is called by the framework at the appropriate time.
        It should never be called by user code.

        """
        super(InstrManagerPlugin, self).start()
        self._refresh_drivers()
        self._refresh_profiles_map()
        self._refresh_users()
        self._bind_observers()

    def stop(self):
        """ Stop the plugin life-cycle.

        This method is called by the framework at the appropriate time.
        It should never be called by user code.

        """
        super(InstrManagerPlugin, self).stop()
        self._unbind_observers()
        self._users.clear()
        self._driver_types.clear()
        self._drivers.clear()
        self._profiles_map.clear()
        self._used_profiles.clear()

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
        return {key: val for key, val in self._driver_types.iteritems()
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

    def profile_path(self, profile):
        """ Request the path of the file storing a profile

        Beware this path should not be used to establish a during communication
        with an instrument as it by-pass the manager securities.

        Parameters
        ----------
        profile : str
            Name of the profile for which the path to its file should be
            returned.

        Returns
        -------
        path : unicode
            The absolute path to the file in which the profile is stored

        """
        return self._profiles_map[profile]

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
            core = self.workbench.get_plugin('enaml.workbench.core')
            for meth, profs in to_release.iteritems():
                res = core.invoke_command(meth, {'profiles': profs}, self)
                if not res:
                    return False, {}

        # Now that we are sure that the profiles can be sent to the users,
        # remove them from the available_profiles list, register who is using
        # them,  and load them
        avail = self.available_profiles
        self.available_profiles = [prof for prof in avail
                                   if prof in profiles]

        used = {prof: new_owner for prof in profiles}
        self._used_profiles.update(used)

        mapping = self._profiles_map
        profile_objects = {prof: open_profile(mapping[prof])
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

    def matching_drivers(self, driver_types):
        """ List the existing drivers whose type is in the specified list

        Parameters
        ----------
        driver_types : list(str)
            Names of the driver types for which matching drivers should be
            returned

        Returns
        -------
        drivers : list(str)
            Names of the matching drivers

        """
        drivers = []
        for d_type in driver_types:
            drivs = [driv for driv, d_class in self._drivers.iteritems()
                     if issubclass(d_class, self._driver_types[d_type])]
            drivers.extend(drivs)

        return drivers

    def matching_profiles(self, drivers):
        """ List the existing profiles whose driver is in the specified list

        Parameters
        ----------
        drivers : list(str)
            Names of the drivers for which matching profiles should be returned

        Returns
        -------
        profiles : list(str)
            Names of the matching profiles

        """
        profiles = []
        for driver in drivers:
            profs = [prof for prof, path in self._profiles_map.iteritems()
                     if open_profile(path)['driver_class'] == driver]
            profiles.extend(profs)

        return profiles

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
    _users = Dict(Unicode(), Typed(InstrUser))

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
                prof_path = os.path.join(path, filename)
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
        failed = {}

        modules = self._explore_package('drivers', path, failed)

        driver_types = {}
        driver_packages = []
        drivers = {}
        self._explore_modules(modules, driver_types, driver_packages, drivers,
                              failed, 'drivers')

        # Remove packages which should not be explored
        for pack in driver_packages[:]:
            if pack in self.drivers_loading:
                driver_packages.remove(pack)

        # Explore packages
        while driver_packages:
            pack = driver_packages.pop(0)
            pack_path = os.path.join(MODULE_PATH, *pack.split('.'))

            modules = self._explore_package(pack, pack_path, failed)

            self._explore_modules(modules, driver_types, driver_packages,
                                  drivers, failed, prefix=pack)

            # Remove packages which should not be explored
            for pack in driver_packages[:]:
                if pack in self.drivers_loading:
                    driver_packages.remove(pack)

        self._drivers = drivers
        self._driver_types = driver_types

        self.driver_types = driver_types.keys()
        self.drivers = drivers.keys()

        # TODO do something with failed

    def _explore_package(self, pack, pack_path, failed):
        """ Explore a package

        Parameters
        ----------
        pack : str
            The package name relative to "drivers". (ex : drivers.visa)

        pack_path : unicode
            Path of the package to explore

        failed : dict
            A dict in which failed imports will be stored.

        Returns
        -------
        modules : list
            List of string indicating modules which can be imported

        """
        if not os.path.isdir(pack_path):
            log = logging.getLogger(__name__)
            mess = '{} is not a valid directory.({})'.format(pack,
                                                             pack_path)
            log.error(mess)
            failed[pack] = mess
            return []

        modules = sorted(pack + '.' + m[:-3] for m in os.listdir(pack_path)
                         if (os.path.isfile(os.path.join(pack_path, m))
                             and m.endswith('.py')))
        try:
            modules.remove(pack + '.__init__')
        except ValueError:
            log = logging.getLogger(__name__)
            mess = cleandoc('''{} is not a valid Python package (miss
                __init__.py).'''.format(pack))
            log.error(mess)
            failed[pack] = mess
            return []

        # Remove modules which should not be imported
        for mod in modules[:]:
            if mod in self.drivers_loading:
                modules.remove(mod)

        return modules

    @staticmethod
    def _explore_modules(modules, types, packages, drivers, failed,
                         prefix):
        """ Explore a list of modules.

        Parameters
        ----------
        modules : list
            The list of modules to explore

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
                m = import_module('.' + mod, MODULE_ANCHOR)
            except Exception as e:
                log = logging.getLogger(__name__)
                mess = 'Failed to import {} : {}'.format(mod, e.message)
                log.error(mess)
                failed[mod] = mess
                continue

            if hasattr(m, 'DRIVER_TYPES'):
                types.update(m.DRIVER_TYPES)

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
                user = self._load_user(extension)
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

        for folder in self.profiles_folders:
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
        removing the extension, adding spaces between 'aA' sequences and
        capitalizing the first letter.

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
        print 'File created'
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
