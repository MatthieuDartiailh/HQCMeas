# -*- coding: utf-8 -*-
#==============================================================================
# module : workspace.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
import logging
import os
import enaml
from atom.api import Typed, Value, set_default
from enaml.application import deferred_call
from enaml.workbench.ui.api import Workspace

from .debugger_plugin import DebuggerPlugin

with enaml.imports():
    from .debugger_content import DebuggerContent, DebuggerMenus


LOG_ID = u'hqc_meas.debug.workspace'


class MeasureSpace(Workspace):
    """
    """
    #--- Public API -----------------------------------------------------------

    # Reference to the plugin to which the workspace is linked.
    plugin = Typed(DebuggerPlugin)

    # Reference to the log panel model received from the log plugin.
    log_model = Value()

    window_title = set_default('Debug')

    def start(self):
        """
        """
        plugin = self.workbench.get_plugin(u'hqc_meas.debug')
        plugin.workspace = self
        self.plugin = plugin

        # Add handler to the root logger to display messages in panel.
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'hqc_meas.logging.add_handler'
        self.log_model = core.invoke_command(cmd,
                                             {'id': LOG_ID, 'mode': 'ui'},
                                             self)[0]

        # Create content.
        self.content = DebuggerContent(workspace=self)

        # Contribute menus.
        self.workbench.register(DebuggerMenus())
        
        # TODO create and dispose dock item for the existing debuggers

    def stop(self):
        """
        """
        # Remove handler from the root logger.
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'hqc_meas.logging.remove_handler'
        core.invoke_command(cmd, {'id': LOG_ID}, self)

        self.plugin.workspace = None
        
    def create_debugger(self):
        """ Create a debugger panel and add a reference to it in the plugin.
        
        """
        pass

    @property
    def dock_area(self):
        """ Getter for the dock_area of the content.

        """
        if self.content and self.content.children:
            return self.content.children[0]

    #--- Private API ----------------------------------------------------------


