# -*- coding: utf-8 -*-
#==============================================================================
# module : tast_base_pulses.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from nose.tools import assert_equal, assert_is, assert_true, assert_false
from hqc_meas.pulses.pulses import (RootSequence, Sequence, Pulse,
                                    ConditionalSequence)
from hqc_meas.pulses.shapes.base_shapes import SquareShape
from hqc_meas.pulses.shapes.modulation import Modulation
from hqc_meas.pulses.contexts.base_context import BaseContext


def test_sequence_indexing1():
    # Test adding, moving, deleting pulse in a sequence.
    root = RootSequence()
    context = BaseContext()
    root.context = context

    pulse1 = Pulse()
    pulse2 = Pulse()
    pulse3 = Pulse()

    root.items.append(pulse1)
    assert_equal(pulse1.index, 1)
    assert_is(pulse1.context, context)
    assert_is(pulse1.root, root)
    assert_equal(root.linkable_vars, ['1_start', '1_stop', '1_duration'])

    root.items.append(pulse2)
    assert_equal(pulse1.index, 1)
    assert_equal(pulse2.index, 2)
    assert_is(pulse2.context, context)
    assert_is(pulse2.root, root)
    assert_equal(root.linkable_vars, ['1_start', '1_stop', '1_duration',
                                      '2_start', '2_stop', '2_duration'])

    root.items.append(pulse3)
    assert_equal(pulse1.index, 1)
    assert_equal(pulse2.index, 2)
    assert_equal(pulse3.index, 3)
    assert_is(pulse3.context, context)
    assert_is(pulse3.root, root)
    assert_equal(root.linkable_vars, ['1_start', '1_stop', '1_duration',
                                      '2_start', '2_stop', '2_duration',
                                      '3_start', '3_stop', '3_duration'])

    root.items.remove(pulse2)
    assert_equal(pulse1.index, 1)
    assert_equal(pulse2.index, 0)
    assert_equal(pulse3.index, 2)
    assert_is(pulse2.context, None)
    assert_is(pulse2.root, None)
    assert_equal(root.linkable_vars, ['1_start', '1_stop', '1_duration',
                                      '2_start', '2_stop', '2_duration'])

    root.items.insert(1, pulse2)
    assert_equal(pulse1.index, 1)
    assert_equal(pulse2.index, 2)
    assert_equal(pulse3.index, 3)
    assert_is(pulse2.context, context)
    assert_is(pulse2.root, root)
    assert_equal(root.linkable_vars, ['1_start', '1_stop', '1_duration',
                                      '2_start', '2_stop', '2_duration',
                                      '3_start', '3_stop', '3_duration'])


def test_sequence_indexing2():
    # Test adding, moving, deleting a sequence in a sequence.
    root = RootSequence()
    context = BaseContext()
    root.context = context

    pulse1 = Pulse()
    pulse2 = Pulse()
    pulse3 = Pulse()
    pulse4 = Pulse()

    sequence1 = Sequence()
    sequence2 = Sequence()

    root.items.append(pulse1)
    root.items.append(sequence1)
    root.items.append(pulse2)

    assert_is(sequence1.parent, root)
    assert_is(sequence1.root, root)
    assert_is(sequence1.context, context)

    sequence1.items.append(sequence2)

    assert_is(sequence2.parent, sequence1)
    assert_is(sequence2.root, root)
    assert_is(sequence2.context, context)
    assert_equal(pulse1.index, 1)
    assert_equal(pulse2.index, 4)
    assert_equal(root.linkable_vars, ['1_start', '1_stop', '1_duration',
                                      '4_start', '4_stop', '4_duration'])

    pulse1.index = 200
    sequence2.items.append(pulse3)

    assert_equal(pulse2.index, 5)
    assert_equal(pulse3.index, 4)
    assert_equal(root.linkable_vars, ['1_start', '1_stop', '1_duration',
                                      '4_start', '4_stop', '4_duration',
                                      '5_start', '5_stop', '5_duration'])
    # Check that only the pulse below the modified sequence are updated.
    assert_equal(pulse1.index, 200)
    pulse1.index = 1

    sequence1.items.insert(0, pulse4)

    assert_equal(pulse4.index, 3)
    assert_equal(sequence2.index, 4)
    assert_equal(pulse3.index, 5)
    assert_equal(pulse2.index, 6)
    assert_equal(root.linkable_vars, ['1_start', '1_stop', '1_duration',
                                      '3_start', '3_stop', '3_duration',
                                      '5_start', '5_stop', '5_duration',
                                      '6_start', '6_stop', '6_duration'])

    sequence1.items = [pulse4]

    assert_is(sequence2.parent, None)
    assert_equal(sequence2.index, 0)
    assert_equal(pulse2.index, 4)
    assert_equal(root.linkable_vars, ['1_start', '1_stop', '1_duration',
                                      '3_start', '3_stop', '3_duration',
                                      '4_start', '4_stop', '4_duration'])

    sequence1.index = 200
    root2 = RootSequence()
    sequence2.root = root2
    sequence2.items = []

    # Check the observer was properly removed
    assert_equal(sequence1.index, 200)


#def test_walking_sequence():
#    pass


def test_eval_pulse1():
    # Test evaluating the entries of a pulse when everything is ok.
    # Start/Stop mode, meaningful values.
    pulse = Pulse()
    pulse.def_1 = '1.0*2.0'
    pulse.def_2 = '5.0*{a}/{b} + {c}'

    local_vars = {'a': 2.0, 'b': 5.0, 'c': 1.0}
    missing = set()
    errors = {}

    assert_true(pulse.eval_entries(local_vars, missing, errors))

    assert_equal(missing, set())
    assert_equal(errors, {})
    assert_equal(pulse.start, 2.0)
    assert_equal(pulse.stop, 3.0)
    assert_equal(pulse.duration, 1.0)


def test_eval_pulse2():
    # Test evaluating the entries of a pulse when everything is ok.
    # Start/Stop mode, meaningless values.
    pulse = Pulse()
    pulse.def_1 = '1.0*2.0'
    pulse.def_2 = '5.0*{a}/{b} + {c}'

    local_vars = {'a': 2.0, 'b': 10.0, 'c': 1.0}
    save = local_vars.copy()
    missing = set()
    errors = {}

    assert_false(pulse.eval_entries(local_vars, missing, errors))

    assert_equal(missing, set())
    assert_equal(errors,
                 {'0_duration': 'Got a negative or null value for duration'})
    assert_equal(local_vars, save)


def test_eval_pulse3():
    # Test evaluating the entries of a pulse when some vars are missing.
    pass


def test_eval_pulse4():
    # Test evaluating the entries of a pulse when some entries are incorrect.
    pass


def test_eval_pulse5():
    # Test evaluating the entries of an analogical pulse.
    pass


def test_eval_pulse6():
    # Test evaluating the entries of an analogical pulse whose modulation
    # evaluation fails.
    pass


def test_eval_pulse7():
    # Test evaluating the entries of an analogical pulse whose shape
    # evaluation fails.
    pass


def test_eval_modulation1():
    # Test evaluating the entries of an inactive modulation.
    pass


def test_eval_modulation2():
    # Text evaluating the entries of an active modulation.
    pass


def test_eval_modulation3():
    # Text evaluating the entries of an active modulation when some vars are
    # missing.
    pass


def test_eval_modulation4():
    # Text evaluating the entries of an active modulation when some entries
    # are incorrect.
    pass


def test_sequence_compilation1():
    # Test compiling a flat sequence.
    pass


def test_sequence_compilation2():
    # Test compiling a flat sequence in two passes.
    pass


def test_sequence_compilation3():
    # Test comiling a flat sequence with circular references.
    pass


def test_sequence_compilation4():
    # Test comiling a flat sequence with evaluation errors.
    pass


def test_sequence_compilation5():
    # Test compiling a nested sequence.
    pass


def test_sequence_compilation6():
    # Test compiling a nested sequence in two passes on the external sequence.
    pass


def test_sequence_compilation7():
    # Test compiling a nested sequence with circular reference in the deep one.
    pass


def test_sequence_compilation8():
    # Test compiling a nested sequence with errors in the deep one.
    pass


def test_conditional_sequence_compilation1():
    # Test compiling a conditional sequence whose condition evaluates to False.
    pass


def test_conditional_sequence_compilation2():
    # Test compiling a conditional sequence whose condition evaluates to True.
    pass


def test_root_sequence_compilation():
    pass
