# -*- coding: utf-8 -*-
# =============================================================================
# module : tast_base_pulses.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from nose.tools import (assert_equal, assert_is, assert_true, assert_false,
                        assert_not_in, assert_in)
from hqc_meas.pulses.pulses import (RootSequence, Sequence, Pulse)
from hqc_meas.pulses.contexts.base_context import BaseContext
from hqc_meas.pulses.shapes.base_shapes import SquareShape
from hqc_meas.utils.walks import flatten_walk


def test_flat_sequence_persistence1():
    # Test writing a flat pulse sequence to a ConfigObj.
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


def test_nested_sequence_persistence1():
    # Test writing a nested pulse sequence to a ConfigObj.
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_variables = {'a': 1.5}

    pulse1 = Pulse(def_1='1.0', def_2='{a}')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
    pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10',
                   kind='analogical', shape=SquareShape())
    seq = Sequence(items=[Pulse(def_1='{2_stop} + 0.5', def_2='10',
                                kind='analogical', shape=SquareShape())])
    root.items.extend([pulse1, pulse2, pulse3, seq])

    pref = root.preferences_from_members()
    assert_equal(pref.keys(),
                 ['external_variables', 'item_class',
                  'sequence_duration', 'enabled', 'fix_sequence_duration',
                  'item_0', 'item_1', 'item_2', 'item_3',
                  'context'])
    assert_equal(pref['item_3'].keys(),
                 ['item_class', 'enabled', 'item_0'])


def test_walk_sequence():
    # Test walking a pulse sequence.
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_variables = {'a': 1.5}

    pulse1 = Pulse(def_1='1.0', def_2='{a}')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
    pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10',
                   kind='analogical', shape=SquareShape())
    seq = Sequence(items=[Pulse(def_1='{2_stop} + 0.5', def_2='10',
                                kind='analogical', shape=SquareShape())])
    root.items.extend([pulse1, pulse2, pulse3, seq])

    walk = root.walk(['item_class', 'shape.shape_class'], {})

    flat = flatten_walk(walk, ['item_class', 'shape.shape_class'])
    assert_in('item_class', flat)
    assert_equal(flat['item_class'],
                 set(['Pulse', 'RootSequence', 'Sequence']))
    assert_in('shape.shape_class', flat)
    assert_equal(flat['shape.shape_class'], set(['SquareShape']))
