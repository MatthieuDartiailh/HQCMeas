# -*- coding: utf-8 -*-
#==============================================================================
# module : base_header.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import Callable
from enaml.core.declarative import Declarative, d_


class Header(Declarative):
    """ Extension for the 'engines' extension point of a MeasurePlugin.

    """

    # Function returning the contributed header.
    build_header = d_(Callable())
