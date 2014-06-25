# -*- coding: utf-8 -*-
#==============================================================================
# module : context.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import Float
from hqc_meas.pulses.contexts.base_context import BaseContext


class TestContext(BaseContext):
    """


    """
    sampling = Float(1.0)

    def _get_sampling_time(self):
        return self.sampling
