# -*- coding: utf-8 -*-
from collections import defaultdict
from enaml.workbench.core.core_plugin import CorePlugin
from enaml.workbench.core.command import Command
from enaml.workbench.core.execution_event import ExecutionEvent

COMMANDS_POINT = u'hqc_meas.core.commands'


class HqcCorePlugin(CorePlugin):
    """ The core plugin for the HQC workbench. Reimplement invoke command to
    returnvalues

    """
    def invoke_command(self, command_id, parameters={}, trigger=None):
        """ Invoke the command handler for the given command id.

        Parameters
        ----------
        command_id : unicode
            The unique identifier of the command to invoke.

        parameters : dict, optional
            The parameters to pass to the command handler.

        trigger : object, optional
            The object which triggered the command.

        """
        if command_id not in self._commands:
            msg = "'%s' is not a registered command id"
            raise ValueError(msg % command_id)

        command = self._commands[command_id]

        event = ExecutionEvent()
        event.command = command
        event.workbench = self.workbench
        event.parameters = parameters
        event.trigger = trigger

        return command.handler(event)

    def _refresh_commands(self):
        """ Refresh the command objects for the plugin.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(COMMANDS_POINT)
        extensions = point.extensions
        if not extensions:
            self._commands.clear()
            self._command_extensions.clear()
            return

        new_extensions = defaultdict(list)
        old_extensions = self._command_extensions
        for extension in extensions:
            if extension in old_extensions:
                commands = old_extensions[extension]
            else:
                commands = self._load_commands(extension)
            new_extensions[extension].extend(commands)

        commands = {}
        for extension in extensions:
            for command in new_extensions[extension]:
                if command.id in commands:
                    msg = "command '%s' is already registered"
                    raise ValueError(msg % command.id)
                if command.handler is None:
                    msg = "command '%s' does not declare a handler"
                    raise ValueError(msg % command.id)
                commands[command.id] = command

        self._commands = commands
        self._command_extensions = new_extensions

    def _load_commands(self, extension):
        """ Load the command objects for the given extension.

        Parameters
        ----------
        extension : Extension
        The extension object of interest.

        Returns
        -------
        result : list
        The list of Command objects declared by the extension.

        """
        workbench = self.workbench
        commands = extension.get_children(Command)
        if extension.factory is not None:
            for item in extension.factory(workbench):
                if not isinstance(item, Command):
                    msg = "extension '%s' created non-Command of type '%s'"
                    args = (extension.qualified_id, type(item).__name__)
                    raise TypeError(msg % args)
                commands.append(item)
        return commands

    def _bind_observers(self):
        """ Setup the observers for the plugin.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(COMMANDS_POINT)
        point.observe('extensions', self._on_commands_updated)

    def _unbind_observers(self):
        """ Remove the observers for the plugin.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(COMMANDS_POINT)
        point.unobserve('extensions', self._on_commands_updated)
