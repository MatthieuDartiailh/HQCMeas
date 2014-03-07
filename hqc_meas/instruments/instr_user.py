# -*- coding: utf-8 -*-
#==============================================================================
# module : instr_user.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""

from atom.api import (Unicode, Enum)
from enaml.core.declarative import Declarative, d_


class InstrUser(Declarative):
    """Extension to the 'instr_users' extensions point of the ManagerPlugin.

    Attributes
    ----------
    release_command : unicode
        Id of the command to call when the ManagerPlugin needs to get an
        instrument profile back from its current user. It will pass a list
        of profiles to release. It should return a bool indicating whether
        or not the operation succeeded. The released_profiles command must
        not be called by the release_method.

    default_policy:
        Does by default the user allows the manager to get the profile back
        when needed.

    """
    release_command = d_(Unicode())

    default_policy = d_(Enum('releasable', 'unreleasable'))
