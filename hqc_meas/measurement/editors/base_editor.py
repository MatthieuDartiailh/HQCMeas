# -*- coding: utf-8 -*-
#==============================================================================
# module : base_engine.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================

from atom.api import Atom, Callable, Unicode, Instance
from enaml.core.declarative import Declarative, d_

from hqc_meas.tasks.api import BaseTask


class BaseEditor(Atom):
    """
    """
    selected_task = Instance(BaseTask)


class Editor(Declarative):
    """ Extension for the 'editors' extension point of a MeasurePlugin.

    """
    # Editor description.
    description = d_(Unicode())

    # Factory function returning an instance of the editor.
    factory = d_(Callable())

    # Test function determining if the editor is fit to be used for the
    # selected task.
    test = d_(Callable())
