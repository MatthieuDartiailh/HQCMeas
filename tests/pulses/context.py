# -*- coding: utf-8 -*-
# =============================================================================
# module : tests/pulses/context.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from atom.api import Float, set_default
from hqc_meas.pulses.contexts.base_context import BaseContext


class TestContext(BaseContext):
    """

    """
    logical_channels = set_default(('Ch1_L', 'Ch2_L'))

    analogical_channels = set_default(('Ch1_A', 'Ch2_A'))

    sampling = Float(1.0)

    def _get_sampling_time(self):
        return self.sampling
