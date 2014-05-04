# -*- coding: utf-8 -*-
#==============================================================================
# module : app_closing.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================

from atom.api import Callable, Unicode
from enaml.core.declarative import Declarative, d_


class ClosingApp(Declarative):
    """ Declarative class for defining a workbench closing app contribution.

    ClosingApp object can be contributed as extensions child to the 'closing'
    extension point of the 'hqc_meas.app' plugin. ClosingApp object are used
    to customize the application behavior on exit.

    Attributes
    ----------
    id : unicode
        The globally unique identifier for the closing.

    validate : callable(window, event)
        A callable performing checks ensuring that the application can be
        safely exited and setting the event (CloseEvent) accordingly.

    """
    id = d_(Unicode())

    validate = d_(Callable())
