# -*- coding: utf-8 -*-
#==============================================================================
# module : preferences.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================

from atom.api import List, Str, Callable
from enaml.core.declarative import Declarative, d_


class Preferences(Declarative):
    """ Declarative class for defining a workbench preference contribution.

    Preferences object can be contributed as extensions child to the 'prefs'
    extension point of a preference plugin.

    Attributes
    ----------
    saving_method : str
        Name of the method of the plugin contributing this extension to call
        when the preference plugin need to save the preferences.

    loading_method : str
        Name of the method of the plugin contributing this extension to call
        when the preference plugin need to load preferences.

    auto_save : list(str)
        The list of plugin members whose values should be observed and whose
        update should cause and automatic update of the preferences.

    edit_view : callable
        A callable returning an autonomous enaml view (Container) used to edit
        the preferences. It should have a model attribute. The model members
        must correspond to the tagged members the plugin, their values will be
        used to update the preferences.

    """
    saving_method = d_(Str('preferences_from_members'))

    loading_method = d_(Str('update_members_from_preferences'))

    auto_save = d_(List(Str()))

    edit_view = d_(Callable())
