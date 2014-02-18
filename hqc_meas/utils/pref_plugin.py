# -*- coding: utf-8 -*-
#==============================================================================
# module : pref_plugin.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================

from atom.api import List, Str, Subclass
from enaml.workbench.api import Plugin
from enaml.core.declarative import Declarative, d_
from enaml.core.enamldef_meta import EnamlDefMeta


class Preferences(Declarative):
    """
    """
    saving_method = d_(Str())

    loading_method = d_(Str())

    auto_save = d_(List(Str()))

    edit_view = d_(Subclass(EnamlDefMeta))


class PrefPlugin(Plugin):
    """
    """
