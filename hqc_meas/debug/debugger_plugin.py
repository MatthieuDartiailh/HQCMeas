# -*- coding: utf-8 -*-
#==============================================================================
# module : debugger_plugin.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
import logging
from collections import defaultdict
from atom.api import (Typed, Unicode, Dict, List, Tuple, ForwardTyped,
                      Value)
from importlib import import_module
import enaml

from hqc_meas.utils.has_pref_plugin import HasPrefPlugin
from .debugger import Debugger


DEBUGGERS_POINT = u'hqc_meas.debug.debuggers'


def _workspace():
    from .debugger_workspace import DebuggerSpace
    return DebuggerSpace


class DebuggerPlugin(HasPrefPlugin):
    """
    """
    #--- Public API -----------------------------------------------------------
    #: List of (module_path, manifest_name) which should be regitered on
    #: startup.
    manifests = List(Tuple()).tag(pref=True)

    #: Reference to the workspace if any.
    workspace = ForwardTyped(_workspace)

    #: Dict holding the contributed Debugger declarations.
    debuggers = Dict(Unicode(), Typed(Debugger))

    #: List of active debuggers.
    debugger_instances = List()

    #: Workspace layout used when reopening the workspace.
    workspace_layout = Value()

    def start(self):
        """
        """
        super(DebuggerPlugin, self).start()

        # Register contributed plugin.
        for path, manifest_name in self.manifests:
            self._register_manifest(path, manifest_name)

        # Refresh contribution and start observers.
        self._refresh_debuggers()
        self._bind_observers()

    def stop(self):
        """
        """
        # Unbind the observers.
        self._unbind_observers()

        # Unregister the plugin registered at start-up.
        for manifest_id in self._manifest_ids:
            self.workbench.unregister(manifest_id)

        # Clear ressources.
        self.debuggers.clear()

    #--- Private API ----------------------------------------------------------

    # Manifests ids of the plugin registered at start up.
    _manifest_ids = List(Unicode())

    # Dict storing which extension declared which editor.
    _debugger_extensions = Typed(defaultdict, (list,))

    def _register_manifest(self, path, manifest_name):
        """ Register a manifest given its module name and its name.

        NB : the path should be a dot separated string referring to a package
        in sys.path. It should be an absolute path.

        """
        try:
            with enaml.imports():
                module = import_module(path)
            manifest = getattr(module, manifest_name)
            plugin = manifest()
            self.workbench.register(plugin)
            self._manifest_ids.append(plugin.id)

        except Exception:
            logger = logging.getLogger(__name__)
            logger.error('Failed to register manifest: {}'.format(path))

    def _refresh_debuggers(self):
        """ Refresh the list of known engines.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(DEBUGGERS_POINT)
        extensions = point.extensions
        if not extensions:
            self.debuggers.clear()
            self._debugger_extensions.clear()
            return

        # Get the engines declarations for all extensions.
        new_extensions = defaultdict(list)
        old_extensions = self._debugger_extensions
        for extension in extensions:
            if extension in old_extensions:
                debuggers = old_extensions[extension]
            else:
                debuggers = self._load_debuggers(extension)
            new_extensions[extension].extend(debuggers)

        # Create mapping between engine id and declaration.
        debuggers = {}
        for extension in extensions:
            for debugger in new_extensions[extension]:
                if debugger.id in debuggers:
                    msg = "debugger '%s' is already registered"
                    raise ValueError(msg % debugger.id)
                if debugger.factory is None:
                    msg = "debugger '%s' does not declare a factory"
                    raise ValueError(msg % debugger.id)
                if debugger.view is None:
                    msg = "debugger '%s' does not declare a view"
                    raise ValueError(msg % debugger.id)
                debuggers[debugger.id] = debugger

        self.debuggers = debuggers
        self._debugger_extensions = new_extensions

    def _load_debuggers(self, extension):
        """ Load the Debugger objects for the given extension.

        Parameters
        ----------
        extension : Extension
            The extension object of interest.

        Returns
        -------
        engines : list(Debugger)
            The Debuggers objects declared by the extension.

        """
        workbench = self.workbench
        debuggers = extension.get_children(Debugger)
        if extension.factory is not None and not debuggers:
            for debugger in extension.factory(workbench):
                if not isinstance(debugger, Debugger):
                    msg = "extension '%s' created non-Debugger."
                    args = (extension.qualified_id)
                    raise TypeError(msg % args)
                debuggers.append(debugger)

        return debuggers

    def _bind_observers(self):
        """ Setup the observers for the plugin.

        """
        workbench = self.workbench

        point = workbench.get_extension_point(DEBUGGERS_POINT)
        point.observe('extensions', self._update_debuggers)

    def _unbind_observers(self):
        """ Remove the observers for the plugin.

        """
        workbench = self.workbench

        point = workbench.get_extension_point(DEBUGGERS_POINT)
        point.unobserve('extensions', self._update_debuggers)

    def _update_debuggers(self, change):
        """
        """
        self._refresh_debuggers()
