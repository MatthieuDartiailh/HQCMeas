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
from hqc_meas.pulses.shapes.base_shapes import SquareShape
from hqc_meas.pulses.shapes.modulation import Modulation
from hqc_meas.pulses.contexts.base_context import BaseContext


def test_sequence_indexing1():
    # Test adding, moving, deleting pulse in a sequence.
    root = RootSequence()
    root.fix_sequence_duration = True
    root.sequence_duration = '1.0'
    context = BaseContext()
    root.context = context

    pulse1 = Pulse()
    pulse2 = Pulse()
    pulse3 = Pulse()

    root.items.append(pulse1)
    assert_equal(pulse1.index, 1)
    assert_is(pulse1.context, context)
    assert_is(pulse1.root, root)
    assert_equal(root.linkable_vars, ['sequence_end',
                                      '1_start', '1_stop', '1_duration'])

    root.items.append(pulse2)
    assert_equal(pulse1.index, 1)
    assert_equal(pulse2.index, 2)
    assert_is(pulse2.context, context)
    assert_is(pulse2.root, root)
    assert_equal(root.linkable_vars, ['sequence_end',
                                      '1_start', '1_stop', '1_duration',
                                      '2_start', '2_stop', '2_duration'])

    root.items.append(pulse3)
    assert_equal(pulse1.index, 1)
    assert_equal(pulse2.index, 2)
    assert_equal(pulse3.index, 3)
    assert_is(pulse3.context, context)
    assert_is(pulse3.root, root)
    assert_equal(root.linkable_vars, ['sequence_end',
                                      '1_start', '1_stop', '1_duration',
                                      '2_start', '2_stop', '2_duration',
                                      '3_start', '3_stop', '3_duration'])

    root.fix_sequence_duration = False
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
    assert_in('0_start', local_vars)
    assert_in('0_stop', local_vars)
    assert_in('0_duration', local_vars)
    assert_equal(pulse.start, 2.0)
    assert_equal(pulse.stop, 3.0)
    assert_equal(pulse.duration, 1.0)


def test_eval_pulse2():
    # Test evaluating the entries of a pulse when everything is ok.
    # Start/Stop mode, meaningless start.
    pulse = Pulse()
    pulse.def_1 = '-1.0*2.0'
    pulse.def_2 = '5.0*{a}/{b} + {c}'

    local_vars = {'a': 2.0, 'b': 10.0, 'c': 1.0}
    missing = set()
    errors = {}

    assert_false(pulse.eval_entries(local_vars, missing, errors))

    assert_equal(missing, set())
    assert_in('0_start', errors)
    assert_not_in('0_start', local_vars)
    assert_not_in('0_duration', local_vars)


def test_eval_pulse3():
    # Test evaluating the entries of a pulse when everything is ok.
    # Start/Stop mode, meaningless stop (0).
    pulse = Pulse()
    pulse.def_1 = '1.0*2.0'
    pulse.def_2 = '5.0*{a}/{b} + {c}'

    local_vars = {'a': 0.0, 'b': 10.0, 'c': 0.0}
    missing = set()
    errors = {}

    assert_false(pulse.eval_entries(local_vars, missing, errors))

    assert_equal(missing, set())
    assert_in('0_stop', errors)
    assert_not_in('0_stop', local_vars)
    assert_not_in('0_duration', local_vars)


def test_eval_pulse4():
    # Test evaluating the entries of a pulse when everything is ok.
    # Start/Stop mode, meaningless stop < start.
    pulse = Pulse()
    pulse.def_1 = '1.0*2.0'
    pulse.def_2 = '5.0*{a}/{b} + {c}'

    local_vars = {'a': 0.0, 'b': 10.0, 'c': 1.0}
    missing = set()
    errors = {}

    assert_false(pulse.eval_entries(local_vars, missing, errors))

    assert_equal(missing, set())
    assert_in('0_stop', errors)
    assert_not_in('0_stop', local_vars)
    assert_not_in('0_duration', local_vars)


def test_eval_pulse5():
    # Test evaluating the entries of a pulse when everything is ok.
    # Start/Duration mode, meaningful values.
    pulse = Pulse()
    pulse.def_mode = 'Start/Duration'
    pulse.def_1 = '1.0*2.0'
    pulse.def_2 = '5.0*{a}/{b} + {c}'

    local_vars = {'a': 2.0, 'b': 5.0, 'c': 1.0}
    missing = set()
    errors = {}

    assert_true(pulse.eval_entries(local_vars, missing, errors))

    assert_equal(missing, set())
    assert_equal(errors, {})
    assert_in('0_start', local_vars)
    assert_in('0_stop', local_vars)
    assert_in('0_duration', local_vars)
    assert_equal(pulse.start, 2.0)
    assert_equal(pulse.stop, 5.0)
    assert_equal(pulse.duration, 3.0)


def test_eval_pulse6():
    # Test evaluating the entries of a pulse when everything is ok.
    # Start/Duration mode, meaningless start.
    pulse = Pulse()
    pulse.def_mode = 'Start/Duration'
    pulse.def_1 = '-1.0*2.0'
    pulse.def_2 = '5.0*{a}/{b} + {c}'

    local_vars = {'a': 0.0, 'b': 10.0, 'c': 1.0}
    missing = set()
    errors = {}

    assert_false(pulse.eval_entries(local_vars, missing, errors))

    assert_equal(missing, set())
    assert_in('0_start', errors)
    assert_not_in('0_start', local_vars)
    assert_not_in('0_stop', local_vars)


def test_eval_pulse7():
    # Test evaluating the entries of a pulse when everything is ok.
    # Start/Duration mode, meaningless duration.
    pulse = Pulse()
    pulse.def_mode = 'Start/Duration'
    pulse.def_1 = '1.0*2.0'
    pulse.def_2 = '5.0*{a}/{b} + {c}'

    local_vars = {'a': 0.0, 'b': 10.0, 'c': 0.0}
    missing = set()
    errors = {}

    assert_false(pulse.eval_entries(local_vars, missing, errors))

    assert_equal(missing, set())
    assert_in('0_duration', errors)
    assert_not_in('0_duration', local_vars)
    assert_not_in('0_stop', local_vars)


def test_eval_pulse8():
    # Test evaluating the entries of a pulse when everything is ok.
    # Duration/Stop mode, meaningful values.
    pulse = Pulse()
    pulse.def_mode = 'Duration/Stop'
    pulse.def_1 = '1.0*2.0'
    pulse.def_2 = '5.0*{a}/{b} + {c}'

    local_vars = {'a': 2.0, 'b': 5.0, 'c': 1.0}
    missing = set()
    errors = {}

    assert_true(pulse.eval_entries(local_vars, missing, errors))

    assert_equal(missing, set())
    assert_equal(errors, {})
    assert_in('0_start', local_vars)
    assert_in('0_stop', local_vars)
    assert_in('0_duration', local_vars)
    assert_equal(pulse.start, 1.0)
    assert_equal(pulse.stop, 3.0)
    assert_equal(pulse.duration, 2.0)


def test_eval_pulse9():
    # Test evaluating the entries of a pulse when everything is ok.
    # Duration/Stop mode, meaningless duration.
    pulse = Pulse()
    pulse.def_mode = 'Duration/Stop'
    pulse.def_1 = '-1.0*2.0'
    pulse.def_2 = '5.0*{a}/{b} + {c}'

    local_vars = {'a': 0.0, 'b': 10.0, 'c': 1.0}
    missing = set()
    errors = {}

    assert_false(pulse.eval_entries(local_vars, missing, errors))

    assert_equal(missing, set())
    assert_in('0_duration', errors)
    assert_not_in('0_duration', local_vars)
    assert_not_in('0_start', local_vars)


def test_eval_pulse10():
    # Test evaluating the entries of a pulse when everything is ok.
    # Duration/Stop mode, meaningless stop.
    pulse = Pulse()
    pulse.def_mode = 'Duration/Stop'
    pulse.def_1 = '1.0*2.0'
    pulse.def_2 = '5.0*{a}/{b} + {c}'

    local_vars = {'a': 0.0, 'b': 10.0, 'c': 0.0}
    missing = set()
    errors = {}

    assert_false(pulse.eval_entries(local_vars, missing, errors))

    assert_equal(missing, set())
    assert_in('0_stop', errors)
    assert_not_in('0_stop', local_vars)
    assert_not_in('0_start', local_vars)


def test_eval_pulse11():
    # Test evaluating the entries of a pulse when everything is ok.
    # Duration/Stop mode, duration larger than stop.
    pulse = Pulse()
    pulse.def_mode = 'Duration/Stop'
    pulse.def_1 = '1.0*2.0'
    pulse.def_2 = '5.0*{a}/{b} + {c}'

    local_vars = {'a': 0.0, 'b': 10.0, 'c': 1.0}
    missing = set()
    errors = {}

    assert_false(pulse.eval_entries(local_vars, missing, errors))

    assert_equal(missing, set())
    assert_in('0_stop', errors)
    assert_not_in('0_start', local_vars)


def test_eval_pulse12():
    # Test evaluating the entries of a pulse when some vars are missing.
    # Issue in def_1
    pulse = Pulse()
    pulse.def_1 = '1.0*2.0*{d}'
    pulse.def_2 = '5.0*{a}/{b} + {c}'

    local_vars = {'a': 2.0, 'b': 10.0, 'c': 1.0}
    missing = set()
    errors = {}

    assert_false(pulse.eval_entries(local_vars, missing, errors))

    assert_equal(missing, set('d'))
    assert_not_in('0_start', errors)
    assert_not_in('0_start', local_vars)
    assert_in('0_stop', local_vars)


def test_eval_pulse13():
    # Test evaluating the entries of a pulse when some vars are missing.
    # Issue in def_2
    pulse = Pulse()
    pulse.def_1 = '1.0*2.0'
    pulse.def_2 = '5.0*{a}/{b} + {c}'

    local_vars = {'a': 2.0, 'b': 10.0}
    missing = set()
    errors = {}

    assert_false(pulse.eval_entries(local_vars, missing, errors))

    assert_equal(missing, set('c'))
    assert_not_in('0_stop', errors)
    assert_not_in('0_stop', local_vars)
    assert_in('0_start', local_vars)


def test_eval_pulse14():
    # Test evaluating the entries of a pulse when some entries are incorrect.
    # Issue def_1
    pulse = Pulse()
    pulse.def_1 = '1.0*2.0*zeffer'
    pulse.def_2 = '5.0*{a}/{b} + {c}'

    local_vars = {'a': 2.0, 'b': 10.0, 'c': 1.0}
    missing = set()
    errors = {}

    assert_false(pulse.eval_entries(local_vars, missing, errors))

    assert_equal(missing, set())
    assert_in('0_start', errors)
    assert_not_in('0_start', local_vars)
    assert_in('0_stop', local_vars)


def test_eval_pulse15():
    # Test evaluating the entries of a pulse when some entries are incorrect.
    # Issue in def_2
    pulse = Pulse()
    pulse.def_1 = '1.0*2.0'
    pulse.def_2 = '5.0*{a}/{b} + {c} + zeffer'

    local_vars = {'a': 2.0, 'b': 10.0, 'c': 1.0}
    missing = set()
    errors = {}

    assert_false(pulse.eval_entries(local_vars, missing, errors))

    assert_equal(missing, set())
    assert_in('0_stop', errors)
    assert_not_in('0_stop', local_vars)
    assert_in('0_start', local_vars)


def test_eval_pulse16():
    # Test evaluating the entries of an analogical pulse.
    pulse = Pulse()
    pulse.def_1 = '1.0*2.0'
    pulse.def_2 = '5.0*{a}/{b} + {c}'

    pulse.shape = SquareShape(amplitude='0.5')
    pulse.kind = 'analogical'

    pulse.context = BaseContext()

    local_vars = {'a': 2.0, 'b': 5.0, 'c': 1.0}
    missing = set()
    errors = {}

    assert_true(pulse.eval_entries(local_vars, missing, errors))

    assert_equal(missing, set())
    assert_equal(errors, {})
    assert_equal(pulse.compute(2.5), 0.5)


def test_eval_pulse17():
    # Test evaluating the entries of an analogical pulse whose modulation
    # evaluation fails.
    pulse = Pulse()
    pulse.def_1 = '1.0*2.0'
    pulse.def_2 = '5.0*{a}/{b} + {c}'

    pulse.shape = SquareShape(amplitude='0.5')
    pulse.kind = 'analogical'

    pulse.modulation.amplitude = '1.0*frfe'
    pulse.modulation.frequency = '1.0'
    pulse.modulation.phase = '1.0'
    pulse.modulation.activated = True

    pulse.context = BaseContext()

    local_vars = {'a': 2.0, 'b': 5.0, 'c': 1.0}
    missing = set()
    errors = {}

    assert_false(pulse.eval_entries(local_vars, missing, errors))

    assert_equal(missing, set())
    assert_in('0_mod_amplitude', errors)


def test_eval_pulse18():
    # Test evaluating the entries of an analogical pulse whose shape
    # evaluation fails.
    pulse = Pulse()
    pulse.def_1 = '1.0*2.0'
    pulse.def_2 = '5.0*{a}/{b} + {c}'

    pulse.shape = SquareShape(amplitude='0.5*')
    pulse.kind = 'analogical'

    pulse.modulation.amplitude = '1.0'
    pulse.modulation.frequency = '1.0'
    pulse.modulation.phase = '1.0'
    pulse.modulation.activated = True

    pulse.context = BaseContext()

    local_vars = {'a': 2.0, 'b': 5.0, 'c': 1.0}
    missing = set()
    errors = {}

    assert_false(pulse.eval_entries(local_vars, missing, errors))

    assert_equal(missing, set())
    assert_in('0_shape_amplitude', errors)


def test_eval_modulation1():
    # Test evaluating the entries of an inactive modulation.
    modulation = Modulation()
    local_vars = {'a': 1.0}
    missing = set()
    errors = {}

    assert_true(modulation.eval_entries(local_vars, missing, errors, 0))
    assert_equal(missing, set())
    assert_equal(errors, {})
    assert_equal(modulation.compute(0, 'mus'), 1.0)


def test_eval_modulation2():
    # Test evaluating the entries of an active modulation.
    modulation = Modulation(activated=True)
    modulation.amplitude = '1.0*{a}'
    modulation.frequency = '1.0'
    modulation.phase = '0.0'

    local_vars = {'a': 1.0}
    missing = set()
    errors = {}

    assert_true(modulation.eval_entries(local_vars, missing, errors, 0))
    assert_equal(missing, set())
    assert_equal(errors, {})
    assert_equal(modulation.compute(0, 'mus'), 0)
    assert_equal(modulation.compute(0.25, 'mus'), 1.0)


def test_eval_modulation3():
    # Test evaluating the entries of an active modulation when some vars are
    # missing.
    # Issue on amplitude.
    modulation = Modulation(activated=True)
    modulation.amplitude = '1.0*{a}'
    modulation.frequency = '1.0'
    modulation.phase = '0.0'

    local_vars = {}
    missing = set()
    errors = {}

    assert_false(modulation.eval_entries(local_vars, missing, errors, 0))
    assert_equal(missing, set('a'))
    assert_in('0_mod_amplitude', errors)


def test_eval_modulation4():
    # Test evaluating the entries of an active modulation when some vars are
    # missing.
    # Issue on frequency.
    modulation = Modulation(activated=True)
    modulation.amplitude = '1.0'
    modulation.frequency = '1.0*{a}'
    modulation.phase = '0.0'

    local_vars = {}
    missing = set()
    errors = {}

    assert_false(modulation.eval_entries(local_vars, missing, errors, 0))
    assert_equal(missing, set('a'))
    assert_in('0_mod_frequency', errors)


def test_eval_modulation5():
    # Test evaluating the entries of an active modulation when some vars are
    # missing.
    # Issue on phase.
    modulation = Modulation(activated=True)
    modulation.amplitude = '1.0'
    modulation.frequency = '1.0'
    modulation.phase = '0.0*{a}'

    local_vars = {}
    missing = set()
    errors = {}

    assert_false(modulation.eval_entries(local_vars, missing, errors, 0))
    assert_equal(missing, set('a'))
    assert_in('0_mod_phase', errors)


def test_eval_modulation6():
    # Test evaluating the entries of an active modulation when some entries
    # are incorrect.
    # Issue on amplitude.
    modulation = Modulation(activated=True)
    modulation.amplitude = '1.0*'
    modulation.frequency = '1.0'
    modulation.phase = '0.0'

    local_vars = {}
    missing = set()
    errors = {}

    assert_false(modulation.eval_entries(local_vars, missing, errors, 0))
    assert_equal(missing, set())
    assert_in('0_mod_amplitude', errors)


def test_eval_modulation7():
    # Test evaluating the entries of an active modulation when some entries
    # are incorrect.
    # Issue on frequency.
    modulation = Modulation(activated=True)
    modulation.amplitude = '1.0'
    modulation.frequency = '1.0*'
    modulation.phase = '0.0'

    local_vars = {}
    missing = set()
    errors = {}

    assert_false(modulation.eval_entries(local_vars, missing, errors, 0))
    assert_equal(missing, set())
    assert_in('0_mod_frequency', errors)


def test_eval_modulation8():
    # Test evaluating the entries of an active modulation when some entries
    # are incorrect.
    # Issue on phase.
    modulation = Modulation(activated=True)
    modulation.amplitude = '1.0'
    modulation.frequency = '1.0'
    modulation.phase = '0.0*'

    local_vars = {}
    missing = set()
    errors = {}

    assert_false(modulation.eval_entries(local_vars, missing, errors, 0))
    assert_equal(missing, set())
    assert_in('0_mod_phase', errors)


def test_eval_modulation9():
    # Test evaluating modulation with too large amplitude.
    modulation = Modulation(activated=True)
    modulation.amplitude = '2.0'
    modulation.frequency = '1.0'
    modulation.phase = '0.0*'

    local_vars = {}
    missing = set()
    errors = {}

    assert_false(modulation.eval_entries(local_vars, missing, errors, 0))
    assert_equal(missing, set())
    assert_in('0_mod_amplitude', errors)


def test_sequence_compilation1():
    # Test compiling a flat sequence.
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_variables = {'a': 1.5}

    pulse1 = Pulse(def_1='1.0', def_2='{a}')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
    pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10')
    root.items.extend([pulse1, pulse2, pulse3])

    res, pulses = root.compile_sequence(False)
    assert_true(res)
    assert_equal(len(pulses), 3)
    assert_equal(pulses[0].start, 1.0)
    assert_equal(pulses[0].stop, 1.5)
    assert_equal(pulses[0].duration, 0.5)
    assert_equal(pulses[1].start, 2.5)
    assert_equal(pulses[1].stop, 3.0)
    assert_equal(pulses[1].duration, 0.5)
    assert_equal(pulses[2].start, 3.5)
    assert_equal(pulses[2].stop, 10.0)
    assert_equal(pulses[2].duration, 6.5)


def test_sequence_compilation2():
    # Test compiling a flat sequence of fixed duration.
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_variables = {'a': 1.5}
    root.fix_sequence_duration = True
    root.sequence_duration = '10.0'

    pulse1 = Pulse(def_1='1.0', def_2='{a}')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
    pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='{sequence_end}')
    root.items.extend([pulse1, pulse2, pulse3])

    res, pulses = root.compile_sequence(False)
    assert_true(res)
    assert_equal(len(pulses), 3)
    assert_equal(pulses[0].start, 1.0)
    assert_equal(pulses[0].stop, 1.5)
    assert_equal(pulses[0].duration, 0.5)
    assert_equal(pulses[1].start, 2.5)
    assert_equal(pulses[1].stop, 3.0)
    assert_equal(pulses[1].duration, 0.5)
    assert_equal(pulses[2].start, 3.5)
    assert_equal(pulses[2].stop, 10.0)
    assert_equal(pulses[2].duration, 6.5)


def test_sequence_compilation3():
    # Test compiling a flat sequence in two passes.
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_variables = {'a': 1.5}

    pulse1 = Pulse(def_1='1.0', def_2='{2_start} - 1.0')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
    pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10')
    root.items.extend([pulse1, pulse2, pulse3])

    res, pulses = root.compile_sequence(False)
    assert_true(res)
    assert_equal(len(pulses), 3)
    assert_equal(pulses[0].start, 1.0)
    assert_equal(pulses[0].stop, 1.5)
    assert_equal(pulses[0].duration, 0.5)
    assert_equal(pulses[1].start, 2.5)
    assert_equal(pulses[1].stop, 3.0)
    assert_equal(pulses[1].duration, 0.5)
    assert_equal(pulses[2].start, 3.5)
    assert_equal(pulses[2].stop, 10.0)
    assert_equal(pulses[2].duration, 6.5)


def test_sequence_compilation4():
    # Test compiling a flat sequence with circular references.
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_variables = {'a': 1.5}

    pulse1 = Pulse(def_1='1.0', def_2='{2_start} - 1.0')
    pulse2 = Pulse(def_1='{1_stop} + 1.0', def_2='3.0')
    pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10')
    root.items.extend([pulse1, pulse2, pulse3])

    res, (missings, errors) = root.compile_sequence(False)
    assert_false(res)
    assert_equal(len(missings), 2)
    assert_in('1_stop', missings)
    assert_in('2_start', missings)
    assert_equal(len(errors), 0)


def test_sequence_compilation5():
    # Test compiling a flat sequence with evaluation errors.
    # missing global
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.fix_sequence_duration = True
    root.sequence_duration = '10.0'

    pulse1 = Pulse(def_1='1.0', def_2='{a}')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
    pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='{sequence_end}')
    root.items.extend([pulse1, pulse2, pulse3])

    res, (missings, errors) = root.compile_sequence(False)
    assert_false(res)
    assert_equal(len(missings), 1)
    assert_in('a', missings)
    assert_equal(len(errors), 0)


def test_sequence_compilation6():
    # Test compiling a flat sequence with evaluation errors.
    # wrong string value
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_variables = {'a': 1.5}
    root.fix_sequence_duration = True
    root.sequence_duration = '*10.0*'

    pulse1 = Pulse(def_1='1.0', def_2='{a}')
    pulse2 = Pulse(def_1='{a} +* 1.0', def_2='3.0')
    pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10.0')
    root.items.extend([pulse1, pulse2, pulse3])

    res, (missings, errors) = root.compile_sequence(False)
    assert_false(res)
    assert_false(missings)
    assert_equal(len(errors), 2)
    assert_in('2_start', errors)
    assert_in('root_seq_duration', errors)


def test_sequence_compilation7():
    # Test compiling a nested sequence.
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_variables = {'a': 1.5}

    pulse1 = Pulse(def_1='1.0', def_2='{a}')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
    pulse3 = Pulse(def_1='{3_stop} + 0.5', def_2='10.0')
    pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
    pulse5 = Pulse(def_1='3.0', def_2='0.5', def_mode='Start/Duration')

    sequence2 = Sequence(items=[pulse3])
    sequence1 = Sequence(items=[pulse2, sequence2, pulse4])

    root.items = [pulse1, sequence1, pulse5]

    res, pulses = root.compile_sequence(False)
    assert_true(res)
    assert_equal(len(pulses), 5)
    assert_is(pulses[0], pulse1)
    assert_equal(pulses[0].start, 1.0)
    assert_equal(pulses[0].stop, 1.5)
    assert_equal(pulses[0].duration, 0.5)
    assert_is(pulses[1], pulse2)
    assert_equal(pulses[1].start, 2.5)
    assert_equal(pulses[1].stop, 3.0)
    assert_equal(pulses[1].duration, 0.5)
    assert_is(pulses[2], pulse3)
    assert_equal(pulses[2].start, 3.5)
    assert_equal(pulses[2].stop, 10.0)
    assert_equal(pulses[2].duration, 6.5)
    assert_is(pulses[3], pulse4)
    assert_equal(pulses[3].start, 2.0)
    assert_equal(pulses[3].stop, 2.5)
    assert_equal(pulses[3].duration, 0.5)
    assert_is(pulses[4], pulse5)
    assert_equal(pulses[4].start, 3.0)
    assert_equal(pulses[4].stop, 3.5)
    assert_equal(pulses[4].duration, 0.5)


def test_sequence_compilation8():
    # Test compiling a nested sequence in two passes on the external sequence.
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_variables = {'a': 1.5}

    pulse1 = Pulse(def_1='1.0', def_2='{7_start} - 1.0')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
    pulse3 = Pulse(def_1='{3_stop} + 0.5', def_2='10.0')
    pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
    pulse5 = Pulse(def_1='3.0', def_2='0.5', def_mode='Start/Duration')

    sequence2 = Sequence(items=[pulse3])
    sequence1 = Sequence(items=[pulse2, sequence2, pulse4])

    root.items = [pulse1, sequence1, pulse5]

    res, pulses = root.compile_sequence(False)
    assert_true(res)
    assert_equal(len(pulses), 5)
    assert_is(pulses[0], pulse1)
    assert_equal(pulses[0].start, 1.0)
    assert_equal(pulses[0].stop, 2.0)
    assert_equal(pulses[0].duration, 1.0)
    assert_is(pulses[1], pulse2)
    assert_equal(pulses[1].start, 2.5)
    assert_equal(pulses[1].stop, 3.0)
    assert_equal(pulses[1].duration, 0.5)
    assert_is(pulses[2], pulse3)
    assert_equal(pulses[2].start, 3.5)
    assert_equal(pulses[2].stop, 10.0)
    assert_equal(pulses[2].duration, 6.5)
    assert_is(pulses[3], pulse4)
    assert_equal(pulses[3].start, 2.0)
    assert_equal(pulses[3].stop, 2.5)
    assert_equal(pulses[3].duration, 0.5)
    assert_is(pulses[4], pulse5)
    assert_equal(pulses[4].start, 3.0)
    assert_equal(pulses[4].stop, 3.5)
    assert_equal(pulses[4].duration, 0.5)


def test_sequence_compilation9():
    # Test compiling a nested sequence in multi passes.
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_variables = {'a': 1.5}

    pulse1 = Pulse(def_1='1.0', def_2='{7_start} - 1.0')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='{6_start} + 1.0')
    pulse3 = Pulse(def_1='{3_stop} + 0.5', def_2='10.0')
    pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
    pulse5 = Pulse(def_1='3.0', def_2='0.5', def_mode='Start/Duration')

    sequence2 = Sequence(items=[pulse3])
    sequence1 = Sequence(items=[pulse2, sequence2, pulse4])

    root.items = [pulse1, sequence1, pulse5]

    res, pulses = root.compile_sequence(False)
    assert_true(res)
    assert_equal(len(pulses), 5)
    assert_is(pulses[0], pulse1)
    assert_equal(pulses[0].start, 1.0)
    assert_equal(pulses[0].stop, 2.0)
    assert_equal(pulses[0].duration, 1.0)
    assert_is(pulses[1], pulse2)
    assert_equal(pulses[1].start, 2.5)
    assert_equal(pulses[1].stop, 3.0)
    assert_equal(pulses[1].duration, 0.5)
    assert_is(pulses[2], pulse3)
    assert_equal(pulses[2].start, 3.5)
    assert_equal(pulses[2].stop, 10.0)
    assert_equal(pulses[2].duration, 6.5)
    assert_is(pulses[3], pulse4)
    assert_equal(pulses[3].start, 2.0)
    assert_equal(pulses[3].stop, 2.5)
    assert_equal(pulses[3].duration, 0.5)
    assert_is(pulses[4], pulse5)
    assert_equal(pulses[4].start, 3.0)
    assert_equal(pulses[4].stop, 3.5)
    assert_equal(pulses[4].duration, 0.5)


def test_sequence_compilation10():
    # Test compiling a nested sequence with circular reference in the deep one.
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_variables = {'a': 1.5}

    pulse1 = Pulse(def_1='1.0', def_2='{7_start} - 1.0')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='{6_start} + 1.0')
    pulse3 = Pulse(def_1='{3_stop} + 0.5', def_2='10.0')
    pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
    pulse5 = Pulse(def_1='{1_stop}', def_2='0.5', def_mode='Start/Duration')

    sequence2 = Sequence(items=[pulse3])
    sequence1 = Sequence(items=[pulse2, sequence2, pulse4])

    root.items = [pulse1, sequence1, pulse5]

    res, (missings, errors) = root.compile_sequence(False)
    assert_false(res)
    assert_equal(len(missings), 2)
    assert_in('7_start', missings)
    assert_in('1_stop', missings)
    assert_false(errors)


def test_sequence_compilation11():
    # Test compiling a nested sequence with circular reference in the deep one.
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_variables = {'a': 1.5}

    pulse1 = Pulse(def_1='1.0', def_2='{7_start} - 1.0')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='{6_start} + 1.0')
    pulse3 = Pulse(def_1='{3_stop} + *0.5', def_2='10.0')
    pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
    pulse5 = Pulse(def_1='3.0', def_2='0.5', def_mode='Start/Duration')

    sequence2 = Sequence(items=[pulse3])
    sequence1 = Sequence(items=[pulse2, sequence2, pulse4])

    root.items = [pulse1, sequence1, pulse5]

    res, (missings, errors) = root.compile_sequence(False)
    assert_false(res)
    assert_equal(len(errors), 1)
    assert_in('5_start', errors)


def test_conditional_sequence_compilation1():
    # Test compiling a conditional sequence whose condition evaluates to False.
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_variables = {'a': 1.5, 'include': True}

    pulse1 = Pulse(def_1='1.0', def_2='{7_start} - 1.0')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
    pulse3 = Pulse(def_1='{3_stop} + 0.5', def_2='10.0')
    pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
    pulse5 = Pulse(def_1='3.0', def_2='0.5', def_mode='Start/Duration')

    sequence2 = Sequence(items=[pulse3])
    sequence1 = ConditionalSequence(items=[pulse2, sequence2, pulse4],
                                    condition='{include}')

    root.items = [pulse1, sequence1, pulse5]

    res, pulses = root.compile_sequence(False)
    assert_true(res)
    assert_equal(len(pulses), 5)
    assert_is(pulses[0], pulse1)
    assert_equal(pulses[0].start, 1.0)
    assert_equal(pulses[0].stop, 2.0)
    assert_equal(pulses[0].duration, 1.0)
    assert_is(pulses[1], pulse2)
    assert_equal(pulses[1].start, 2.5)
    assert_equal(pulses[1].stop, 3.0)
    assert_equal(pulses[1].duration, 0.5)
    assert_is(pulses[2], pulse3)
    assert_equal(pulses[2].start, 3.5)
    assert_equal(pulses[2].stop, 10.0)
    assert_equal(pulses[2].duration, 6.5)
    assert_is(pulses[3], pulse4)
    assert_equal(pulses[3].start, 2.0)
    assert_equal(pulses[3].stop, 2.5)
    assert_equal(pulses[3].duration, 0.5)
    assert_is(pulses[4], pulse5)
    assert_equal(pulses[4].start, 3.0)
    assert_equal(pulses[4].stop, 3.5)
    assert_equal(pulses[4].duration, 0.5)


def test_conditional_sequence_compilation2():
    # Test compiling a conditional sequence whose condition evaluates to True.
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_variables = {'a': 1.5, 'include': False}

    pulse1 = Pulse(def_1='1.0', def_2='{7_start} - 1.0')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
    pulse3 = Pulse(def_1='{3_stop} + 0.5', def_2='10.0')
    pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
    pulse5 = Pulse(def_1='3.0', def_2='0.5', def_mode='Start/Duration')

    sequence2 = Sequence(items=[pulse3])
    sequence1 = ConditionalSequence(items=[pulse2, sequence2, pulse4],
                                    condition='{include}')

    root.items = [pulse1, sequence1, pulse5]

    res, pulses = root.compile_sequence(False)
    assert_true(res)
    assert_equal(len(pulses), 2)
    assert_is(pulses[0], pulse1)
    assert_equal(pulses[0].start, 1.0)
    assert_equal(pulses[0].stop, 2.0)
    assert_equal(pulses[0].duration, 1.0)
    assert_is(pulses[1], pulse5)
    assert_equal(pulses[1].start, 3.0)
    assert_equal(pulses[1].stop, 3.5)
    assert_equal(pulses[1].duration, 0.5)


def test_conditional_sequence_compilation3():
    # Test compiling a conditional sequence whose condition evaluates to True.
    root = RootSequence()
    context = BaseContext()
    root.context = context
    root.external_variables = {'a': 1.5, 'include': False}

    pulse1 = Pulse(def_1='1.0', def_2='{7_start} - 1.0')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
    pulse3 = Pulse(def_1='{3_stop} + 0.5', def_2='10.0')
    pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
    pulse5 = Pulse(def_1='3.0', def_2='0.5', def_mode='Start/Duration')

    sequence2 = Sequence(items=[pulse3])
    sequence1 = ConditionalSequence(items=[pulse2, sequence2, pulse4],
                                    condition='{include}*/')

    root.items = [pulse1, sequence1, pulse5]

    res, (missings, errors) = root.compile_sequence(False)
    assert_false(res)
    assert_in('2_condition', errors)
