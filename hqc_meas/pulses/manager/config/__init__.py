# -*- coding: utf-8 -*-
# =============================================================================
# module : hqc_meas/pulses/manager/config
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================

from ...base_sequences import Sequence
from .base_config import SequenceConfig


# Defining the special config dictionnary used by the builder to select the
# right config task class.
SEQUENCE_CONFIG = {Sequence: SequenceConfig}

import enaml
with enaml.imports():
    from .base_config_views import SimpleView, NoneView

CONFIG_MAP_VIEW = {type(None): NoneView, SequenceConfig: SimpleView}
