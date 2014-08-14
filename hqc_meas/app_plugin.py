# -*- coding: utf-8 -*-
#==============================================================================
# module : app_plugin.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import (Unicode, Dict, Typed)
from enaml.workbench.api import Plugin
from collections import defaultdict
from .app_closing import ClosingApp


CLOSING_POINT = u'hqc_meas.app.closing'


class HqcAppPlugin(Plugin):
    """ A plugin to manage application wide available states

    """

    def start(self):
        """ Start the plugin life-cycle.

        This method is called by the framework at the appropriate time. It
        should never be called by user code.

        """
        self._closing_checks = {}
        self._refresh_closing_checks()
        self._bind_observers()

    def stop(self):
        """ Stop the plugin life-cycle.

        This method is called by the framework at the appropriate time.
        It should never be called by user code.

        """
        self._unbind_observers()
        self._closing_checks.clear()

    def validate_closing(self, window, event):
        """ Run all closing checks to determine whether or not to close the
        app.

        """
        for closing in self._closing_checks.values():
            closing.validate(window, event)
            if not event.is_accepted():
                break

    #---- Private API ---------------------------------------------------------

    _closing_checks = Dict(Unicode(), Typed(ClosingApp))

    # Dict storing which extension declared which editor.
    _closing_extensions = Typed(defaultdict, (list,))

    def _refresh_closing_checks(self):
        """ Refresh the list of states contributed by extensions.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(CLOSING_POINT)
        extensions = point.extensions

        # If no extension remain clear everything
        if not extensions:
            self._closing_checks.clear()
            self._closing_extensions.clear()
            return

        # Get the engines declarations for all extensions.
        new_extensions = defaultdict(list)
        old_extensions = self._closing_extensions
        for extension in extensions:
            if extension in old_extensions:
                closing_checks = old_extensions[extension]
            else:
                closing_checks = self._load_closing_checks(extension)
            new_extensions[extension].extend(closing_checks)

        # Create mapping between engine id and declaration.
        closing_checks = {}
        for extension in extensions:
            for closing_check in new_extensions[extension]:
                if closing_check.id in closing_checks:
                    msg = "closing check '%s' is already registered"
                    raise ValueError(msg % closing_check.id)
                if closing_check.validate is None:
                    msg = "closing check '%s' does not declare a validate"
                    raise ValueError(msg % closing_check.id)
                closing_checks[closing_check.id] = closing_check

        self._closing_checks = closing_checks
        self._closing_extensions = new_extensions

    def _load_closing_checks(self, extension):
        """ Load the Engine object for the given extension.

        Parameters
        ----------
        extension : Extension
            The extension object of interest.

        Returns
        -------
        closing_checks : list(Closing)
            The Closing object declared by the extension.

        """
        workbench = self.workbench
        closings = extension.get_children(ClosingApp)
        if extension.factory is not None and not closings:
            for closing in extension.factory(workbench):
                if not isinstance(closing, ClosingApp):
                    msg = "extension '%s' created non-ClosingApp."
                    args = (extension.qualified_id)
                    raise TypeError(msg % args)
                closings.append(closing)

        return closings

    def _on_closing_checks_updated(self, change):
        """ The observer for the state extension point

        """
        self._refresh_closing_checks()

    def _bind_observers(self):
        """ Setup the observers for the plugin.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(CLOSING_POINT)
        point.observe('extensions', self._on_closing_checks_updated)

    def _unbind_observers(self):
        """ Remove the observers for the plugin.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(CLOSING_POINT)
        point.unobserve('extensions', self._on_closing_checks_updated)
