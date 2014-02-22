# -*- coding: utf-8 -*-
#==============================================================================
# module : pref_plugin.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================

from atom.api import List, Str, Callable
from enaml.workbench.api import Plugin

from .preferences import Preferences

class PrefPlugin(Plugin):
    """

    """

    def start(self):
        """
        """
        pass

    def stop(self):
        """
        """
        pass

    def save_preferences(self, path=None):
        """
        """
        pass

    def load_preferences(self, path=None):
        """
        """
        pass

    def plugin_init_complete(self, plugin_id):
        """
        """
        pass

    def plugin_preferences(self, plugin_id):
        """
        """
        # TODO
        return {}

    def update_plugin_preferences(self, plugin_id):
        """
        """
        pass
