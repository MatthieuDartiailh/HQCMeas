# -*- coding: utf-8 -*-
#==============================================================================
# module : base_header.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import Callable, Unicode
from enaml.core.declarative import Declarative, d_


class Header(Declarative):
    """ Extension for the 'engines' extension point of a MeasurePlugin.

    The name member inherited from Object should always be set to an easily
    understandable name for the user.

    """
    # Id of the header, this can be different from the id of the plugin
    # declaring it but does not have to.
    id = d_(Unicode())

    # Header description.
    description = d_(Unicode())

    # Function returning the contributed header. No arguments.
    build_header = d_(Callable())
