# -*- coding: utf-8 -*-
"""
"""
from atom.api import Atom, Typed, Dict
from enaml.workbench.api import Workbench
from collections import defaultdict

from .dependencies import BuildDependency, RuntimeDependency

BUILD_DEP_POINT = u'hqc_meas.task_manager.build_dependencies'

RUNTIME_DEP_POINT = u'hqc_meas.task_manager.runtime_dependencies'


class BuildDependenciesManager(Atom):
    """ Build-dependencies manager for the TaskManager extension point.

    """
    #--- Public API -----------------------------------------------------------

    #: Reference to the applictaion workbench.
    workbench = Typed(Workbench)

    #: List holding all the build dependency collector.
    collectors = Dict()

    def start(self):
        """ Start the manager.

        """
        self._refresh_build_deps()
        self._bind_observers()

    def stop(self):
        """ Stop the manager.

        """
        self._unbind_observers()
        self.collectors.clear()
        self._extensions.clear()

    #--- Private API ----------------------------------------------------------

    #: Dict storing which extension declared which build dependency.
    _extensions = Typed(defaultdict, (list,))

    def _refresh_build_deps(self):
        """ Refresh the list of known build dependency collectors.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(BUILD_DEP_POINT)
        extensions = point.extensions
        if not extensions:
            self.collectors.clear()
            self._extensions.clear()
            return

        # Get the monitors declarations for all extensions.
        new_extensions = defaultdict(list)
        old_extensions = self._extensions
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

        self.collectors = build_deps
        self._extensions = new_extensions

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

    def _update_build_deps(self, change):
        """

        """
        self._refresh_build_deps()

    def _bind_observers(self):
        """

        """
        point = self.workbench.get_extension_point(BUILD_DEP_POINT)
        point.observe('extensions', self._update_build_deps)

    def _unbind_observers(self):
        """

        """
        point = self.workbench.get_extension_point(BUILD_DEP_POINT)
        point.unobserve('extensions', self._update_build_deps)


class RuntimeDependenciesManager(Atom):
    """ Runtime-dependencies manager for the TaskManager extension point.

    """
    #--- Public API -----------------------------------------------------------

    #: Reference to the applictaion workbench.
    workbench = Typed(Workbench)

    #: List holding all the runtime dependency collectors.
    collectors = Dict()

    def start(self):
        """ Start the manager.

        """
        self._refresh_runtime_deps()
        self._bind_observers()

    def stop(self):
        """ Stop the manager.

        """
        self._unbind_observers()
        self.collectors.clear()
        self._extensions.clear()

    #--- Private API ----------------------------------------------------------

    #: Dict storing which extension declared which runtime dependency.
    _extensions = Typed(defaultdict, (list,))

    def _refresh_runtime_deps(self):
        """ Refresh the list of known monitors.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(RUNTIME_DEP_POINT)
        extensions = point.extensions
        if not extensions:
            self.collectors.clear()
            self._extensions.clear()
            return

        # Get the monitors declarations for all extensions.
        new_extensions = defaultdict(list)
        old_extensions = self._extensions
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

        self.collectors = runtime_deps
        self._extensions = new_extensions

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

    def _bind_observers(self):
        """

        """
        point = self.workbench.get_extension_point(RUNTIME_DEP_POINT)
        point.observe('extensions', self._update_runtime_deps)

    def _unbind_observers(self):
        """

        """
        point = self.workbench.get_extension_point(RUNTIME_DEP_POINT)
        point.unobserve('extensions', self._update_runtime_deps)
