# -*- coding: utf-8 -*-
#==============================================================================
# module : debugger.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import (Atom, Callable, Unicode, Value, ForwardTyped)
from enaml.core.declarative import Declarative, d_


def _debugger_plugin():
    from .debugger_plugin import DebuggerPlugin
    return DebuggerPlugin


class BaseDebugger(Atom):
    """ Base class for all debuggers.

    """
    #: Refrence to the application workbench.
    plugin = ForwardTyped(_debugger_plugin)

    #: Reference to the manifest used for cretaing this debugger.
    declaration = ForwardTyped(lambda: Debugger)

    def release_ressources(self):
        """ Ask the debugger to release all ressources it is actively using.

        This method is called when the activity of the debugger is about to
        stop.

        """
        pass


class Debugger(Declarative):
    """ Extension for the 'debuggers' extension point of a DebuggerPlugin.

    The name member inherited from Object should always be set to an easily
    understandable name for the user.

    """
    #: Id of the debugger, this can be different from the id of the plugin
    #: declaring it but does not have to.
    id = d_(Unicode())

    #: Debugger description.
    description = d_(Unicode())

    #: Factory function returning an instance of the debugger. This callable
    #: should take as arguments the debugger declaration and the debugger
    #: plugin.
    factory = d_(Callable())

    #: View of the debugger or factory taking as args the dock_area,
    #: the debugger and the name of the top widget.
    view = d_(Value())

    #: Callable adding contribution to the main window take as single argument
    #: the workspace.
    contribute_workspace = d_(Callable())

    #: Callable removing the contribution from the main window.
    remove_contribution = d_(Callable())
