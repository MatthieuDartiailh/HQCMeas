# -*- coding: utf-8 -*-
#==============================================================================
# module : base_header.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import Callable, Unicode, Str
from enaml.core.declarative import Declarative, d_


class Header(Declarative):
    """ Extension for the 'engines' extension point of a MeasurePlugin.

    """
    # Id of the header, this can be different from the id of the plugin
    # declaring it but does not have to.
    id = d_(Unicode())

    # Name of the header. This should an easily understandable name for the
    # user.
    name = d_(Str())

    # Header description.
    description = d_(Unicode())

    # Function returning the contributed header. No arguments.
    build_header = d_(Callable())
