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
