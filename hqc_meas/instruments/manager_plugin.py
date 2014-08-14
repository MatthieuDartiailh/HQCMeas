# -*- coding: utf-8 -*-
# =============================================================================
# module : instrument_manager.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
import os
import logging
from importlib import import_module
from atom.api import (Str, Dict, List, Unicode, Typed, Subclass, Tuple)
from enaml.application import deferred_call
import enaml


from watchdog.observers import Observer
from watchdog.events import (FileSystemEventHandler, FileCreatedEvent,
                             FileDeletedEvent, FileMovedEvent)
from inspect import cleandoc, getmodule, getmembers, isclass
from collections import defaultdict

from ..utils.has_pref_plugin import HasPrefPlugin
from .drivers.driver_tools import BaseInstrument
from .instr_user import InstrUser
from .profile_utils import open_profile


USERS_POINT = u'hqc_meas.instr_manager.users'

MODULE_PATH = os.path.dirname(__file__)

MODULE_ANCHOR = 'hqc_meas.instruments'


class InstrManagerPlugin(HasPrefPlugin):
    """
    """
    # --- Public API ----------------------------------------------------------

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
        path = os.path.join(MODULE_PATH, 'profiles')
        if not os.path.isdir(path):
            os.mkdir(path)
        self._refresh_drivers()
        self._refresh_forms()
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
        self._forms.clear()
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
            The required driver types that have been found as a dict
            {name: class}.

        missing : list
            The list of drivers that was not found.

        """
        missing = [driver_type for driver_type in driver_types
                   if driver_type not in self.driver_types]

        found = {key: val for key, val in self._driver_types.iteritems()
                 if key in driver_types}

        return found, missing

    def drivers_request(self, drivers):
        """ Give access to the driver type implementation

        Parameters
        ----------
        drivers : list(str)
            The names of the drivers the user want to get the classes.

        Returns
        -------
        drivers : dict
            The required driver that have been found as a dict {name: class}.

        missing : list
            The list of drivers that was not found.

        """
        missing = [driver for driver in drivers
                   if driver not in self.drivers]

        found = {key: val for key, val in self._drivers.iteritems()
                 if key in drivers}

        return found, missing

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
        path : unicode or None
            The absolute path to the file in which the profile is stored, if
            the profile is known.

        """
        return self._profiles_map.get(profile, None)

    def profiles_request(self, new_owner, profiles):
        """ Register the user of the specified profiles.

        If necessary this method will try to free profiles used by different
        owners, however it might fail in doing so and the client must be able
        to handle.

        Parameters
        ----------
        new_owner : unicode
            Id of the plugin requesting the right to use some profiles

        profiles : list(str)
            The names of the profiles the user want the privilege to use.

        Returns
        -------
        profiles : dict or list
            The required profiles as a dict {name: profile}, can be empty if
            a profile is missing or if the manager failed to release a profile.

        missing : list
            The list of profiles that was not found.

        """
        if new_owner not in self._users:
            logger = logging.getLogger(__name__)
            mess = cleandoc('''Plugin {} tried to request profiles, but it is
                not a registered user.'''.format(new_owner))
            logger.error(mess)
            return {}, []

        missing = [prof for prof in profiles
                   if prof not in self.all_profiles]

        if missing:
            return {}, missing

        to_release = defaultdict(list)
        # Identify the profiles which need to be released
        for prof in profiles:
            if prof in self._used_profiles:
                old_owner = self._used_profiles[prof]
                decl = self._users[old_owner]
                if decl.default_policy == 'unreleasable':
                    return {}, []

                to_release[decl.release_method].append(prof)

        if to_release:
            for meth, profs in to_release.iteritems():
                res = meth(self.workbench, profiles=profs)
                if not res:
                    return {}, []

        # Now that we are sure that the profiles can be sent to the users,
        # remove them from the available_profiles list, register who is using
        # them,  and load them
        avail = self.available_profiles
        self.available_profiles = [prof for prof in avail
                                   if prof not in profiles]

        used = {prof: new_owner for prof in profiles}
        self._used_profiles.update(used)

        mapping = self._profiles_map
        profile_objects = {prof: open_profile(mapping[prof])
                           for prof in profiles}

        return profile_objects, []

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
            try:
                del mapping[prof]
            except KeyError:
                pass

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
                     if open_profile(path)['driver'] == driver]
            profiles.extend(profs)

        return profiles

    def matching_form(self, driver, view=False):
        """ Return the appropriate form to edit a profile for the given driver.

        Parameters
        ----------
        driver : str
            Name of the driver or driver type for which a form should be
            returned.

        view : bool, optionnal
            Whether or not to return the matching view alongside the form.

        Returns
        -------
        form : AbstractConnectionForm
            Form allowing to edit a profile for the given driver.

        view : Enamldef
            View matching the form.

        """
        form, f_view = None, None
        if driver in self._driver_types:
            aux = self._driver_types[driver].__name__
            form, f_view = self._forms.get(aux, (None, None))

        elif driver in self._drivers:
            d_mro = self._drivers[driver].mro()
            i = 1
            while driver not in self._forms and i < len(d_mro):
                driver = d_mro[i].__name__
                i += 1

            form, f_view = self._forms.get(driver, (None, None))

        if form is None:
            logger = logging.getLogger(__name__)
            mes = "No matching form was found for the driver {}".format(driver)
            logger.warn(mes)

        if view:
            return form, f_view
        else:
            return form

    def report(self):
        """ Give access to the failures which happened at startup.

        """
        return self._failed

    def reload_driver(self, driver):
        """ Reload a driver definition.

        All the classes in the driver mro are reloaded in reverse order.

        Parameters
        ----------
        driver : str
            Name of the driver whose definition should be reloaded.

        Returns
        -------
        driver: class
            Reloaded definition of the driver.

        """
        d_class = self._drivers[driver]
        mro = type.mro(d_class)[::-1]
        for ancestor in mro[2::]:
            name = ancestor.__name__
            mod = getmodule(ancestor)
            mod = reload(mod)
            mem = getmembers(mod, isclass)
            reloaded = [m[1] for m in mem if m[0] == name][0]

            if ancestor in self._drivers.values():
                for k, v in self._drivers.iteritems():
                    if v == ancestor:
                        self._drivers[k] = reloaded

            if ancestor in self._driver_types.values():
                for k, v in self._driver_types.iteritems():
                    if v == ancestor:
                        self._driver_types[k] = reloaded

        return self._drivers[driver]

    # --- Private API ---------------------------------------------------------
    # Drivers types
    _driver_types = Dict(Str(), Subclass(BaseInstrument))

    # Drivers
    _drivers = Dict(Str(), Subclass(BaseInstrument))

    # Connections forms and views {driver_name: (form, view)}.
    _forms = Dict(Str(), Tuple())

    # Mapping between profile names and path to .ini file holding the data.
    _profiles_map = Dict(Str(), Unicode())

    # Mapping between profile names and user id.
    _used_profiles = Dict(Unicode(), Unicode())

    # Mapping between plugin_id and InstrUser declaration.
    _users = Dict(Unicode(), Typed(InstrUser))

    # Dict holding the list of failures which happened during loading
    _failed = Dict()

    # Watchdog observer
    _observer = Typed(Observer, ())

    def _refresh_profiles_map(self, deferred=False):
        """ Refresh the known profiles

        """
        profiles = {}
        for path in self.profiles_folders:
            if os.path.isdir(path):
                filenames = sorted(f for f in os.listdir(path)
                                   if (os.path.isfile(os.path.join(path, f))
                                       and f.endswith('.ini')))

                for filename in filenames:
                    profile_name = self._normalise_name(filename)
                    prof_path = os.path.join(path, filename)
                    # Beware redundant names are overwrited
                    profiles[profile_name] = prof_path
            else:
                logger = logging.getLogger(__name__)
                logger.warn('{} is not a valid directory'.format(path))

        if deferred:
            deferred_call(self._set_profiles_map, profiles)
        else:
            self._set_profiles_map(profiles)

    def _set_profiles_map(self, profiles):
        """ Set the known profiles values.

        This function is used for deferred settings to avoid issues with
        watchdog threads.

        """
        self._profiles_map = profiles
        self.all_profiles = sorted(list(profiles.keys()))
        self.available_profiles = [prof for prof in sorted(profiles.keys())
                                   if prof not in self._used_profiles]

    def _refresh_drivers(self):
        """ Refresh the known driver types and drivers.

        """
        path = os.path.join(MODULE_PATH, 'drivers')
        failed = {}

        modules = self._explore_package('drivers', path, failed,
                                        self.drivers_loading)

        driver_types = {}
        driver_packages = []
        drivers = {}
        self._explore_modules_for_drivers(modules, driver_types,
                                          driver_packages, drivers,
                                          failed, 'drivers')

        # Remove packages which should not be explored
        for pack in driver_packages[:]:
            if pack in self.drivers_loading:
                driver_packages.remove(pack)

        # Explore packages
        while driver_packages:
            pack = driver_packages.pop(0)
            pack_path = os.path.join(MODULE_PATH, *pack.split('.'))

            modules = self._explore_package(pack, pack_path, failed,
                                            self.drivers_loading)

            self._explore_modules_for_drivers(modules, driver_types,
                                              driver_packages,
                                              drivers, failed, prefix=pack)

            # Remove packages which should not be explored
            for pack in driver_packages[:]:
                if pack in self.drivers_loading:
                    driver_packages.remove(pack)

        self._drivers = drivers
        self._driver_types = driver_types

        self.driver_types = sorted(driver_types.keys())
        self.drivers = sorted(drivers.keys())
        self._failed = failed
        # TODO do something with failed

    @staticmethod
    def _explore_modules_for_drivers(modules, types, packages, drivers, failed,
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
                mess = 'Failed to import {} : {}'.format(mod, e)
                log.error(mess)
                failed[mod] = mess
                continue

            if hasattr(m, 'DRIVER_TYPES'):
                types.update(m.DRIVER_TYPES)

            if hasattr(m, 'DRIVER_PACKAGES'):
                packs = [prefix + '.' + pack for pack in m.DRIVER_PACKAGES]
                packages.extend(packs)

            if hasattr(m, 'DRIVERS'):
                drivers.update(m.DRIVERS)

    def _refresh_forms(self):
        """ Refresh the list of known forms.

        """
        path = os.path.join(MODULE_PATH, 'forms')
        failed = {}

        modules = self._explore_package('forms', path, failed, [])

        forms = {}
        for mod in modules:
            try:
                m = import_module('.' + mod, MODULE_ANCHOR)
            except Exception as e:
                log = logging.getLogger(__name__)
                mess = 'Failed to import {} : {}'.format(mod, e.message)
                log.error(mess)
                failed[mod] = mess
                continue

            if hasattr(m, 'FORMS'):
                forms.update(m.FORMS)

        path = os.path.join(path, 'views')
        view_modules = self._explore_package('forms.views', path, failed, [],
                                             '.enaml')

        views = {}
        for mod in view_modules:
            try:
                with enaml.imports():
                    m = import_module('.' + mod, MODULE_ANCHOR)
            except Exception as e:
                log = logging.getLogger(__name__)
                mess = 'Failed to import {} : {}'.format(mod, e.message)
                log.error(mess)
                failed[mod] = mess
                continue

            if hasattr(m, 'FORMS_MAP_VIEWS'):
                views.update(m.FORMS_MAP_VIEWS)

        self._forms = {driver: (form, views[form.__name__])
                       for driver, form in forms.iteritems()
                       if form.__name__ in views}

    @staticmethod
    def _explore_package(pack, pack_path, failed, exceptions, suffix='.py'):
        """ Explore a package

        Parameters
        ----------
        pack : str
            The package name relative to "drivers". (ex : drivers.visa)

        pack_path : unicode
            Path of the package to explore

        failed : dict
            A dict in which failed imports will be stored.

        exceptions : list
            List of module which should be ignored

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

        i = len(suffix)
        modules = sorted(pack + '.' + m[:-i] for m in os.listdir(pack_path)
                         if (os.path.isfile(os.path.join(pack_path, m))
                             and m.endswith(suffix)))

        if suffix == '.py':
            try:
                modules.remove(pack + '.__init__')
            except ValueError:
                log = logging.getLogger(__name__)
                mess = cleandoc('''{} is not a valid Python package (miss
                    __init__.py).'''.format(pack))
                log.error(mess)
                failed[pack] = mess
                return []
        else:
            if '__init__.py' not in os.listdir(pack_path):
                log = logging.getLogger(__name__)
                mess = cleandoc('''{} is not a valid Python package (miss
                    __init__.py).'''.format(pack))
                log.error(mess)
                failed[pack] = mess
                return []

        # Remove modules which should not be imported
        for mod in modules[:]:
            if mod in exceptions:
                modules.remove(mod)

        return modules

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
        """ Load the user object for the given extension.

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
                msg = "extension '%s' created non-InstrUser of type '%s'"
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

        self._observer.start()
        self.observe('drivers_loading', self._update_drivers)
        self.observe('profiles_folders', self._update_profiles)

    def _unbind_observers(self):
        """ Remove the observers for the plugin.

        """
        self.unobserve('drivers_loading', self._update_drivers)
        self.unobserve('profiles_folders', self._update_profiles)
        self._observer.unschedule_all()
        self._observer.stop()
        self._observer.join()

        workbench = self.workbench
        point = workbench.get_extension_point(USERS_POINT)
        point.unobserve('extensions', self._on_users_updated)

    def _update_drivers(self, change):
        """ Observer ensuring that loading preferences are taken into account.

        """
        self._refresh_drivers()

    def _update_profiles(self, change):
        """ Observer ensuring that we observe the right profile folders.

        """
        self._observer.unschedule_all()

        for folder in self.profiles_folders:
            handler = _FileListUpdater(self._refresh_profiles_map)
            self._observer.schedule(handler, folder, recursive=True)

    @staticmethod
    def _normalise_name(name):
        """ Normalize the name of the profiles by replacing '_' by spaces,
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
        super(_FileListUpdater, self).on_created(event)
        if isinstance(event, FileCreatedEvent):
            self.handler(True)

    def on_deleted(self, event):
        super(_FileListUpdater, self).on_deleted(event)
        if isinstance(event, FileDeletedEvent):
            self.handler(True)

    def on_moved(self, event):
        super(_FileListUpdater, self).on_moved(event)
        if isinstance(event, FileMovedEvent):
            self.handler(True)
