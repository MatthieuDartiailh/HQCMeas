# -*- coding: utf-8 -*-
#==============================================================================
# module : preferences.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import (List, Str, Dict, Unicode)
from enaml.core.declarative import Declarative, d_


class State(Declarative):
    """ Declarative class for defining a workbench state.

    State object can be contributed as extensions child to the 'states'
    extension point of a state plugin.

    Attributes
    ----------
    id : unicode
        The globally unique identifier for the state

    description : str
        An optional description of what the state provides.

    sync_members : list(str)
        The list of plugin members whose values should be reflected in the
        state object

    prop_getters : dict(str, str)
        Dictionnary mapping property namer of the state object to the name of
        the method on the plugin which can be used as the property getter.

    """
    id = d_(Unicode())

    description = d_(Str())

    # Will be used to dynamically create an atom class with value members,
    # and observe plugin to update state object in consequence
    sync_members = d_(List(Str()))

    # getters to build properties for things that are updated on the model only
    # somebody needs it (Beware don't use in UI as you wouldn't get any updates
    # ). key is the name of the property in the state, value the name of the
    # property getter on the plugin
    prop_getters = d_(Dict(Str(), Str()))
