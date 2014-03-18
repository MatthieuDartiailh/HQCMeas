# -*- coding: utf-8 -*-
#==============================================================================
# module : measure_plugin.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import Bool

from hqc_meas.utils.has_pref_plugin import HasPrefPlugin

class MeasurePlugin(HasPrefPlugin):
    """
    """
    # Have to be here otherwise lost tons of infos when closing workspace
    edited_measure
    enqueued_measures
    running_measure =

    engines
    selected_engine

    monitors
    default_monitors

    checks
    default_checks

    headers
    default_headers




