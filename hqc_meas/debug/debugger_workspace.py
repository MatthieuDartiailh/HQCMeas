# -*- coding: utf-8 -*-
#==============================================================================
# module : debugger_workspace.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
import enaml
from atom.api import Typed, Value, set_default, Bool
from enaml.application import deferred_call
from enaml.workbench.ui.api import Workspace
from enaml.layout.api import InsertItem

from .debugger_plugin import DebuggerPlugin

with enaml.imports():
    from .debugger_content import DebuggerContent, DebuggerMenus


LOG_ID = u'hqc_meas.debug.workspace'


class DebuggerSpace(Workspace):
    """
    """
    #--- Public API -----------------------------------------------------------

    #: Reference to the plugin to which the workspace is linked.
    plugin = Typed(DebuggerPlugin)

    #: Reference to the log panel model received from the log plugin.
    log_model = Value()

    enable_dock_events = Bool(True)

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

        # Add debugger contributions.
        for debugger in self.plugin.debuggers.values():
            if debugger.contribute_workspace:
                debugger.contribute_workspace(self)

        # If the workspace was previously opened restore its state.
        if self.plugin.debugger_instances and self.plugin.workspace_layout:
            deferred_call(self._restore_debuggers)

    def stop(self):
        """
        """
        # If the dock area still exists it means the main window was not
        # destroyed        .
        if self.dock_area:
            self.plugin.workspace_layout = self.dock_area.save_layout()
            # Prevent debugger from being destroyed when the dock_area is
            # destroyed when swapping workspaces.
            self.enable_dock_events = False

        # Ask all the debuggers to release their ressources. (No debugger
        # should run in the background).
        for debugger in self.plugin.debugger_instances:
            debugger.release_ressources()

        # Remove debugger contributions.
        for debugger in self.plugin.debuggers.values():
            if debugger.remove_contribution:
                debugger.remove_contribution(self)

        self.workbench.unregister(u'hqc_meas.debug.menus')

        # Remove handler from the root logger.
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'hqc_meas.logging.remove_handler'
        core.invoke_command(cmd, {'id': LOG_ID}, self)

        self.plugin.workspace = None

    def create_debugger(self, declaration):
        """ Create a debugger panel and add a reference to it in the plugin.

        """
        # Find first unused name.
        dock_numbers = sorted([int(pane.name[5])
                               for pane in self.dock_area.dock_items()
                               if pane.name.startswith('item')])

        if dock_numbers and dock_numbers[-1] > len(dock_numbers):
            first_free = min(set(xrange(1, len(dock_numbers)+1))
                             - set(dock_numbers))
            name = 'item_{}'.format(first_free)
        else:
            name = 'item_{}'.format(len(dock_numbers) + 1)

        debugger = declaration.factory(declaration, self.plugin)
        self.plugin.debugger_instances.append(debugger)
        declaration.view(self.dock_area, debugger=debugger, name=name)
        self.dock_area.update_layout(InsertItem(item=name, target='main_log',
                                                position='top'))

    @property
    def dock_area(self):
        """ Getter for the dock_area of the content.

        """
        if self.content and self.content.children:
            return self.content.children[0]

    #--- Private API ----------------------------------------------------------

    def _restore_debuggers(self):
        """ Restore debuggers from a previous use of the workspace.

        """
        self.enable_dock_events = False
        dock_area = self.dock_area
        for i, debugger in enumerate(self.plugin.debugger_instances):
            name = 'item_{}'.format(i+1)
            debugger.declaration.view(dock_area, debugger=debugger,
                                      name=name)
        dock_area.apply_layout(self.plugin.workspace_layout)
        self.enable_dock_events = True
