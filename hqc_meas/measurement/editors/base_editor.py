# -*- coding: utf-8 -*-
#==============================================================================
# module : base_engine.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================

from atom.api import Atom, Callable
from enaml.core.declarative import Declarative, d_


class BaseEditor(Atom):
    """ Base class for all engines.

    An engine is responsible for performing a measurement given a hierarchical
    ensemble of tasks.

    """
    pass


class Editor(Declarative):
    """ Extension for the 'engines' extension point of a MeasurePlugin.

    """

    # Factory function returning an instance of the editor.
    factory = d_(Callable())
