# -*- coding: utf-8 -*-
# =============================================================================
# module : tast_pulses_persistence.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from nose.tools import (assert_equal, assert_in, assert_is_instance,
                        assert_items_equal)
from hqc_meas.pulses.pulse import Pulse
from hqc_meas.pulses.base_sequences import RootSequence, Sequence
from hqc_meas.pulses.contexts.base_context import BaseContext
from hqc_meas.pulses.shapes.base_shapes import SquareShape
from hqc_meas.utils.walks import flatten_walk


def test_flat_sequence_persistence1():
    # Test writing a flat pulse sequence to a ConfigObj.
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_vars = {'a': 1.5}

    pulse1 = Pulse(def_1='1.0', def_2='{a}')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
    pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10',
                   kind='Analogical', shape=SquareShape())
    root.items.extend([pulse1, pulse2, pulse3])

    pref = root.preferences_from_members()
    assert_items_equal(pref.keys(),
                       ['name', 'local_vars', 'time_constrained',
                        'enabled', 'item_class', 'sequence_duration',
                        'item_0', 'item_1', 'item_2', 'external_vars',
                        'context', 'def_1', 'def_2', 'def_mode'])

    assert_in('shape', pref['item_2'])
    assert_in('shape_class', pref['item_2']['shape'])
    assert_equal(pref['item_2']['shape']['shape_class'], 'SquareShape')


def test_nested_sequence_persistence1():
    # Test writing a nested pulse sequence to a ConfigObj.
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_vars = {'a': 1.5}

    pulse1 = Pulse(def_1='1.0', def_2='{a}')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
    pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10',
                   kind='Analogical', shape=SquareShape())
    seq = Sequence(items=[Pulse(def_1='{2_stop} + 0.5', def_2='10',
                                kind='Analogical', shape=SquareShape())])
    root.items.extend([pulse1, pulse2, pulse3, seq])

    pref = root.preferences_from_members()
    assert_items_equal(pref.keys(),
                       ['name', 'local_vars', 'time_constrained',
                        'enabled', 'item_class', 'sequence_duration',
                        'item_0', 'item_1', 'item_2', 'item_3',
                        'context', 'def_1', 'def_2', 'def_mode',
                        'external_vars'])
    assert_items_equal(pref['item_3'].keys(),
                       ['item_class', 'enabled', 'name', 'item_0',
                        'def_1', 'def_2', 'def_mode', 'local_vars',
                        'time_constrained'])


def test_walk_sequence():
    # Test walking a pulse sequence.
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_vars = {'a': 1.5}

    pulse1 = Pulse(def_1='1.0', def_2='{a}')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
    pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10',
                   kind='Analogical', shape=SquareShape())
    seq = Sequence(items=[Pulse(def_1='{2_stop} + 0.5', def_2='10',
                                kind='Analogical', shape=SquareShape())])
    root.items.extend([pulse1, pulse2, pulse3, seq])

    walk = root.walk(['item_class', 'shape_class'], {})

    flat = flatten_walk(walk, ['item_class', 'shape_class'])
    assert_in('item_class', flat)
    assert_equal(flat['item_class'],
                 set(['Pulse', 'RootSequence', 'Sequence']))
    assert_in('shape_class', flat)
    assert_equal(flat['shape_class'], set(['SquareShape']))


def test_build_from_config():
    # Test building a pulse sequence.
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_vars = {'a': 1.5}

    pulse1 = Pulse(def_1='1.0', def_2='{a}')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
    pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10',
                   kind='Analogical', shape=SquareShape())
    seq = Sequence(items=[Pulse(def_1='{2_stop} + 0.5', def_2='10',
                                kind='Analogical', shape=SquareShape())])
    root.items.extend([pulse1, pulse2, pulse3, seq])

    pref = root.preferences_from_members()
    dependecies = {'pulses': {'Sequence': Sequence, 'Pulse': Pulse,
                              'shapes': {'SquareShape': SquareShape},
                              'contexts': {'BaseContext': BaseContext}}}

    aux = RootSequence.build_from_config(pref, dependecies)
    assert_equal(aux.external_vars, {'a': 1.5})
    assert_equal(len(aux.items), 4)
    assert_is_instance(aux.context, BaseContext)

    pulse1 = aux.items[0]
    assert_equal(pulse1.def_1, '1.0')
    assert_equal(pulse1.def_2, '{a}')

    pulse2 = aux.items[1]
    assert_equal(pulse2.def_1, '{a} + 1.0')
    assert_equal(pulse2.def_2, '3.0')

    pulse3 = aux.items[2]
    assert_equal(pulse3.def_1, '{2_stop} + 0.5')
    assert_equal(pulse3.def_2, '10')
    assert_equal(pulse3.kind, 'Analogical')
    assert_is_instance(pulse3.shape, SquareShape)

    seq = aux.items[3]
    assert_equal(len(seq.items), 1)
