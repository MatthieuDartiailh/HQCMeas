# -*- coding: utf-8 -*-

from enaml.workbench.api import Plugin

from .atom_util import HasPrefAtom


class HasPrefPlugin(Plugin):
    """ Base class for plugin using preferences.

    Simply defines the most basic preferences system herited from HasPrefAtom
    """

    update_members_from_preferences = \
        HasPrefAtom.update_members_from_preferences.__func__

    preferences_from_members = \
        HasPrefAtom.preferences_from_members.__func__

    def start(self):
        """
        """
        core = self.workbench.get_plugin('enaml.workbench.core')

        prefs = core.invoke_command('hqc_meas.preferences.get_plugin_prefs',
                                    {'plugin_id': self.manifest.id}, self)

        self.update_members_from_preferences(**prefs)
        core.invoke_command('hqc_meas.preferences.plugin_init_complete',
                            {'plugin_id': self.manifest.id}, self)

    # This would turn everything in auto which is not desired
#    def stop(self):
#        """
#        """
#        core = self.workbench.get_plugin('hqc_meas.core')
#        core.invoke_command('hqc_meas.preferences.update_plugin_prefs',
#                            parameters={}, trigger=self)
