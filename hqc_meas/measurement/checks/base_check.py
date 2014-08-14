# -*- coding: utf-8 -*-
#==============================================================================
# module : base_engine.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================

from atom.api import Callable, Unicode
from enaml.core.declarative import Declarative, d_


class Check(Declarative):
    """ Extension for the 'engines' extension point of a MeasurePlugin.

    The name member inherited from Object should always be set to an easily
    understandable name for the user.

    """
    # Id of the check, this can be different from the id of the plugin
    # declaring it but does not have to.
    id = d_(Unicode())

    # Check's description.
    description = d_(Unicode())

    # Function running the checks on the task. The expected signature is:
    # perform_check(workbench, root_task) -> result as dict
    perform_check = d_(Callable())
