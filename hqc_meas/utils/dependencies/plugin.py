# -*- coding: utf-8 -*-
# =============================================================================
# module : utils/dependencies/plugin.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import Typed, Dict
from enaml.workbench.api import Plugin
from collections import defaultdict
from inspect import cleandoc
import logging

from hqc_meas.tasks.tools.walks import flatten_walk
from hqc_meas.utils.configobj_ops import flatten_config

from .dependencies import BuildDependency, RuntimeDependency

BUILD_DEP_POINT = u'hqc_meas.dependencies.build'

RUNTIME_DEP_POINT = u'hqc_meas.dependencies.runtime'


class DependenciesManagerPlugin(Plugin):
    """ Build-dependencies manager for the TaskManager extension point.

    """
    # --- Public API ----------------------------------------------------------

    #: List holding all the build dependency collector.
    build_collectors = Dict()

    #: List holding all the runtime dependency collector.
    runtime_collectors = Dict()

    def start(self):
        """ Start the manager.

        """
        self._refresh_build_deps()
        self._refresh_runtime_deps()
        self._bind_observers()

    def stop(self):
        """ Stop the manager.

        """
        self._unbind_observers()
        self.build_collectors.clear()
        self.runtime_collectors.clear()
        self._build_extensions.clear()
        self._runtime_extensions.clear()

    def collect_dependencies(self, obj, dependencies=['build', 'runtime'],
                             caller=None):
        """ Build a dict of dependencies for a given obj.

        NB : This assumes the obj has a walk method similar to the one found
        in ComplexTask

        Parameters
        ----------
        obj : object with a walk method
            Obj for which dependencies should be computed.

        dependencies : {['build'], ['runtime'], ['build', 'runtime']}
            Kind of dependencies which should be gathered.

        Returns
        -------
        result : bool
            Flag indicating the success of the operation.

        dependencies : dict
            In case of success:
            - Dict holding all the classes or other dependencies to build, run
            or build and run a task without any access to the workbench.
            If a single kind of dependencies is requested a single dict is
            returned otherwise two are returned one for the build ones and one
            for the runtime ones

            Otherwise:
            - dict holding the id of the dependencie and the asssociated
            error message.

        """
        # Use a set to avoid collecting several times the same entry, which
        # could happen if an entry is both a build and a runtime dependency.
        members = set()
        callables = {}
        if 'runtime' in dependencies and caller is None:
            raise RuntimeError(cleandoc('''Cannot collect runtime dependencies
                without knowing the caller plugin'''))

        if 'build' in dependencies:
            for build_dep in self.build_collectors.values():
                members.update(set(build_dep.walk_members))

        if 'runtime' in dependencies:
            for runtime_dep in self.runtime_collectors.values():
                members.update(set(runtime_dep.walk_members))
                callables.update(runtime_dep.walk_callables)

        walk = obj.walk(members, callables)
        flat_walk = flatten_walk(walk, list(members) + callables.keys())

        deps = ({}, {})
        errors = {}
        if 'build' in dependencies:
            for build_dep in self.build_collectors.values():
                try:
                    deps[0].update(build_dep.collect(self.workbench,
                                                     flat_walk))
                except ValueError as e:
                    errors[build_dep.id] = e.message

        if 'runtime' in dependencies:
            for runtime_dep in self.runtime_collectors.values():
                try:
                    deps[1].update(runtime_dep.collect(self.workbench,
                                                       flat_walk, caller))
                except ValueError as e:
                    errors[runtime_dep.id] = e.message

        if errors:
            return False, errors

        if 'build' in dependencies and 'runtime' in dependencies:
            return True, deps[0], deps[1]
        elif 'build' in dependencies:
            return True, deps[0]
        else:
            return True, deps[1]

    def collect_build_dep_from_config(self, config):
        """ Read a ConfigObj object to determine all the build dependencies of
        an object and get them in a dict.

        Parameters
        ----------
        manager : TaskManager
            Instance of the task manager.

        coonfig : Section
            Section representing the task hierarchy.

        Returns
        -------
        build_dep : nested dict or None
            Dictionary holding all the build dependencies of an obj.
            With this dict and the config the obj can be reconstructed without
            accessing the workbech.
            None is case of failure.

        """
        members = []
        for build_dep in self.build_collectors.values():
            members.extend(build_dep.walk_members)

        flat_config = flatten_config(config, members)

        build_deps = {}
        for build_dep in self.build_collectors.values():
            try:
                build_deps.update(build_dep.collect(self.workbench,
                                                    flat_config))
            except ValueError as e:
                logger = logging.getLogger(__name__)
                logger.error(e.message)
                return None

        return build_deps

    def report(self):
        """ Give access to the failures which happened at startup.

        """
        return self._failed

    # --- Private API ---------------------------------------------------------

    #: Dict storing which extension declared which build dependency.
    _build_extensions = Typed(defaultdict, (list,))

    #: Dict storing which extension declared which runtime dependency.
    _runtime_extensions = Typed(defaultdict, (list,))

    def _refresh_build_deps(self):
        """ Refresh the list of known build dependency collectors.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(BUILD_DEP_POINT)
        extensions = point.extensions
        if not extensions:
            self.build_collectors.clear()
            self._build_extensions.clear()
            return

        # Get the monitors declarations for all extensions.
        new_extensions = defaultdict(list)
        old_extensions = self._build_extensions
        for extension in extensions:
            if extensions in old_extensions:
                build_deps = old_extensions[extension]
            else:
                build_deps = self._load_build_deps(extension)
            new_extensions[extension].extend(build_deps)

        # Create mapping between monitor id and declaration.
        build_deps = {}
        for extension in extensions:
            for build_dep in new_extensions[extension]:
                if build_dep.id in build_deps:
                    msg = "build_dep '%s' is already registered"
                    raise ValueError(msg % build_dep.id)
                if not build_dep.walk_members:
                    msg = "build_dep '%s' does not declare any dependencies"
                    raise ValueError(msg % build_dep.id)
                if build_dep.collect is None:
                    msg = "build_dep '%s' does not declare a collect function"
                    raise ValueError(msg % build_dep.id)
                build_deps[build_dep.id] = build_dep

        self.build_collectors = build_deps
        self._build_extensions = new_extensions

    def _load_build_deps(self, extension):
        """ Load the Monitor object for the given extension.

        Parameters
        ----------
        extension : Extension
            The extension object of interest.

        Returns
        -------
        build_deps : list(BuildDependency)
            The list of BuildDependency declared by the extension.

        """
        workbench = self.workbench
        build_deps = extension.get_children(BuildDependency)
        if extension.factory is not None and not build_deps:
            for build_dep in extension.factory(workbench):
                if not isinstance(build_dep, BuildDependency):
                    msg = "extension '%s' created non-Monitor."
                    args = (extension.qualified_id)
                    raise TypeError(msg % args)
                build_deps.append(build_dep)

        return build_deps

    def _refresh_runtime_deps(self):
        """ Refresh the list of known monitors.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(RUNTIME_DEP_POINT)
        extensions = point.extensions
        if not extensions:
            self.runtime_collectors.clear()
            self._runtime_extensions.clear()
            return

        # Get the monitors declarations for all extensions.
        new_extensions = defaultdict(list)
        old_extensions = self._runtime_extensions
        for extension in extensions:
            if extensions in old_extensions:
                runtime_deps = old_extensions[extension]
            else:
                runtime_deps = self._load_runtime_deps(extension)
            new_extensions[extension].extend(runtime_deps)

        # Create mapping between monitor id and declaration.
        runtime_deps = {}
        for extension in extensions:
            for runtime_dep in new_extensions[extension]:
                if runtime_dep.id in runtime_deps:
                    msg = "runtime_dep '%s' is already registered"
                    raise ValueError(msg % runtime_dep.id)
                if not runtime_dep.walk_members\
                        and not runtime_dep.walk_callables:
                    msg = "build_dep '%s' does not declare any dependencies"
                    raise ValueError(msg % runtime_dep.id)
                if runtime_dep.collect is None:
                    msg = "build_dep '%s' does not declare a collect function"
                    raise ValueError(msg % runtime_dep.id)
                runtime_deps[runtime_dep.id] = runtime_dep

        self.runtime_collectors = runtime_deps
        self._runtime_extensions = new_extensions

    def _load_runtime_deps(self, extension):
        """ Load the RuntimeDependency objects for the given extension.

        Parameters
        ----------
        extension : Extension
            The extension object of interest.

        Returns
        -------
        runtime_deps : list(RuntimeDependency)
            The list of RuntimeDependency declared by the extension.

        """
        workbench = self.workbench
        runtime_deps = extension.get_children(RuntimeDependency)
        if extension.factory is not None and not runtime_deps:
            for runtime_dep in extension.factory(workbench):
                if not isinstance(runtime_dep, RuntimeDependency):
                    msg = "extension '%s' created non-RuntimeDependency."
                    args = (extension.qualified_id)
                    raise TypeError(msg % args)
                runtime_deps.append(runtime_dep)

        return runtime_deps

    def _update_runtime_deps(self, change):
        """

        """
        self._refresh_runtime_deps()

    def _update_build_deps(self, change):
        """

        """
        self._refresh_build_deps()

    def _bind_observers(self):
        """

        """
        point = self.workbench.get_extension_point(BUILD_DEP_POINT)
        point.observe('extensions', self._update_build_deps)
        point = self.workbench.get_extension_point(RUNTIME_DEP_POINT)
        point.observe('extensions', self._update_runtime_deps)

    def _unbind_observers(self):
        """

        """
        point = self.workbench.get_extension_point(BUILD_DEP_POINT)
        point.unobserve('extensions', self._update_build_deps)
        point = self.workbench.get_extension_point(RUNTIME_DEP_POINT)
        point.unobserve('extensions', self._update_runtime_deps)
