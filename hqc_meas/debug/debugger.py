# -*- coding: utf-8 -*-
#==============================================================================
# module : debugger.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import (Atom, Callable, Unicode, Value, ForwardTyped,
                      Typed)
from enaml.core.declarative import Declarative, d_
from enaml.workbench.api import Workbench


class BaseDebugger(Atom):
    """ Base class for all debuggers.
    
    """
    #: Refrence to the application workbench.
    workbench = Typed(Workbench)    
    
    #: Reference to the manifest used for cretaing this debugger.
    manifest = ForwardTyped(lambda: Debugger)

class Debugger(Declarative):
    """ Extension for the 'debuggers' extension point of a DebuggerPlugin.

    The name member inherited from Object should always be set to an easily
    understandable name for the user.

    """
    # Id of the debugger, this can be different from the id of the plugin
    # declaring it but does not have to.
    id = d_(Unicode())

    # Debugger description.
    description = d_(Unicode())

    # Factory function returning an instance of the debugger. This callable
    # should take as arguments the debugger declaration and the workbench.
    factory = d_(Callable())
    
    view = d_(Value())
