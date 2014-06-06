# -*- coding: utf-8 -*-
#==============================================================================
# module : tast_base_pulses.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from nose.tools import (assert_equal, assert_is, assert_true, assert_false,
                        assert_not_in, assert_in)
from hqc_meas.pulses.pulses import (RootSequence, Sequence, Pulse,
                                    ConditionalSequence)
from hqc_meas.pulses.contexts.base_context import BaseContext


def test_flat_sequence_persistence1():
    # Test writing a pulse sequence to a ConfigObj.
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_variables = {'a': 1.5}

    pulse1 = Pulse(def_1='1.0', def_2='{a}')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
    pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10')
    root.items.extend([pulse1, pulse2, pulse3])

    pref = root.preferences_from_members()
    assert_equal(pref.keys(),
                 ['external_variables', 'item_class',
                  'sequence_duration', 'enabled', 'fix_sequence_duration',
                  'item_0', 'item_1', 'item_2',
                  'context'])
