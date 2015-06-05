# -*- coding: utf-8 -*-
# =============================================================================
# module : tests/pulses/manager/config/test_base_config.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from nose.tools import assert_true, assert_is_instance

from hqc_meas.pulses.api import Sequence
from hqc_meas.pulses.manager.config.base_config import SequenceConfig


def test_sequence_config():
    # Test sequence config.
    conf = SequenceConfig(sequence_class=Sequence)
    conf.sequence_name = 'test'
    assert_true(conf.config_ready)
    seq = conf.build_sequence()
    assert_is_instance(seq, Sequence)
