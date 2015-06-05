# -*- coding: utf-8 -*-
# =============================================================================
# module : test_base_pulses.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from nose.tools import (assert_equal, assert_is, assert_true, assert_false,
                        assert_not_in, assert_in, assert_items_equal)
from numpy.testing import assert_array_equal
import numpy as np
from hqc_meas.pulses.pulse import Pulse
from hqc_meas.pulses.base_sequences import RootSequence, Sequence
from hqc_meas.pulses.sequences.conditional_sequence import ConditionalSequence
from hqc_meas.pulses.shapes.base_shapes import SquareShape
from hqc_meas.pulses.shapes.modulation import Modulation

from .context import TestContext


def test_sequence_time_constaints_observation():
    # Test adding, moving, deleting pulse in a sequence.
    root = RootSequence()
    context = TestContext()
    root.context = context
    sequence = Sequence()
    root.items = [sequence]

    assert_equal(root.linkable_vars, [])

    sequence.time_constrained = True

    assert_items_equal(root.linkable_vars, ['1_start', '1_stop', '1_duration'])

    sequence.time_constrained = False

    assert_equal(root.linkable_vars, [])


def test_sequence_indexing1():
    # Test adding, moving, deleting pulse in a sequence.
    root = RootSequence()
    root.time_constrained = True
    root.sequence_duration = '1.0'
    context = TestContext()
    root.context = context

    pulse1 = Pulse()
    pulse2 = Pulse()
    pulse3 = Pulse()

    root.items.append(pulse1)
    assert_equal(pulse1.index, 1)
    assert_is(pulse1.root, root)
    assert_items_equal(root.linkable_vars, ['sequence_end',
                                            '1_start', '1_stop', '1_duration'])

    root.items.append(pulse2)
    assert_equal(pulse1.index, 1)
    assert_equal(pulse2.index, 2)
    assert_is(pulse2.root, root)
    assert_items_equal(root.linkable_vars, ['sequence_end',
                                            '1_start', '1_stop', '1_duration',
                                            '2_start', '2_stop', '2_duration'])

    root.items.append(pulse3)
    assert_equal(pulse1.index, 1)
    assert_equal(pulse2.index, 2)
    assert_equal(pulse3.index, 3)
    assert_is(pulse3.root, root)
    assert_items_equal(root.linkable_vars, ['sequence_end',
                                            '1_start', '1_stop', '1_duration',
                                            '2_start', '2_stop', '2_duration',
                                            '3_start', '3_stop', '3_duration'])

    root.time_constrained = False
    root.items.remove(pulse2)
    assert_equal(pulse1.index, 1)
    assert_equal(pulse2.index, 0)
    assert_equal(pulse3.index, 2)
    assert_is(pulse2.root, None)
    assert_items_equal(root.linkable_vars, ['1_start', '1_stop', '1_duration',
                                            '2_start', '2_stop', '2_duration'])

    root.items.insert(1, pulse2)
    assert_equal(pulse1.index, 1)
    assert_equal(pulse2.index, 2)
    assert_equal(pulse3.index, 3)
    assert_is(pulse2.root, root)
    assert_items_equal(root.linkable_vars, ['1_start', '1_stop', '1_duration',
                                            '2_start', '2_stop', '2_duration',
                                            '3_start', '3_stop', '3_duration'])


def test_sequence_indexing2():
    # Test adding, moving, deleting a sequence in a sequence.
    root = RootSequence()
    context = TestContext()
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

    sequence1.items.append(sequence2)

    assert_is(sequence2.parent, sequence1)
    assert_is(sequence2.root, root)
    assert_equal(pulse1.index, 1)
    assert_equal(pulse2.index, 4)
    assert_items_equal(root.linkable_vars, ['1_start', '1_stop', '1_duration',
                                            '4_start', '4_stop', '4_duration'])

    pulse1.index = 200
    sequence2.items.append(pulse3)

    assert_is(pulse3.parent, sequence2)
    assert_is(pulse3.root, root)
    assert_equal(pulse2.index, 5)
    assert_equal(pulse3.index, 4)
    assert_items_equal(root.linkable_vars, ['1_start', '1_stop', '1_duration',
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
    assert_items_equal(root.linkable_vars, ['1_start', '1_stop', '1_duration',
                                            '3_start', '3_stop', '3_duration',
                                            '5_start', '5_stop', '5_duration',
                                            '6_start', '6_stop', '6_duration'])

    sequence1.items = [pulse4]

    assert_is(sequence2.parent, None)
    assert_equal(sequence2.index, 0)
    assert_equal(pulse2.index, 4)
    assert_items_equal(root.linkable_vars, ['1_start', '1_stop', '1_duration',
                                            '3_start', '3_stop', '3_duration',
                                            '4_start', '4_stop', '4_duration'])

    sequence1.index = 200
    root2 = RootSequence()
    sequence2.root = root2
    sequence2.items = []

    # Check the observer was properly removed
    assert_equal(sequence1.index, 200)


class TestPulse(object):

    def setup(self):
        self.pulse = Pulse(root=RootSequence(context=TestContext()))

    def test_eval_pulse1(self):
        # Test evaluating the entries of a pulse when everything is ok.
        # Start/Stop mode, meaningful values.
        self.pulse.def_1 = '1.0*2.0'
        self.pulse.def_2 = '5.0*{a}/{b} + {c}'

        root_vars = {'a': 2.0, 'b': 5.0, 'c': 1.0}
        missing = set()
        errors = {}

        seq_locals = root_vars.copy()
        assert_true(self.pulse.eval_entries(root_vars, seq_locals,
                                            missing, errors))

        assert_equal(missing, set())
        assert_equal(errors, {})
        assert_equal(root_vars['0_start'], 2.0)
        assert_equal(root_vars['0_stop'], 3.0)
        assert_equal(root_vars['0_duration'], 1.0)
        assert_equal(seq_locals['0_start'], 2.0)
        assert_equal(seq_locals['0_stop'], 3.0)
        assert_equal(seq_locals['0_duration'], 1.0)
        assert_equal(self.pulse.start, 2.0)
        assert_equal(self.pulse.stop, 3.0)
        assert_equal(self.pulse.duration, 1.0)
        assert_array_equal(self.pulse.waveform, np.ones(1))

    def test_eval_pulse2(self):
        # Test evaluating the entries of a pulse when everything is ok.
        # Start/Stop mode, meaningless start.
        self.pulse.def_1 = '-1.0*2.0'
        self.pulse.def_2 = '5.0*{a}/{b} + {c}'

        root_vars = {'a': 2.0, 'b': 10.0, 'c': 1.0}
        missing = set()
        errors = {}

        seq_locals = root_vars.copy()
        assert_false(self.pulse.eval_entries(root_vars, seq_locals,
                                             missing, errors))

        assert_equal(missing, set())
        assert_in('0_start', errors)
        assert_not_in('0_start', root_vars)
        assert_not_in('0_duration', root_vars)
        assert_not_in('0_start', seq_locals)
        assert_not_in('0_duration', seq_locals)

    def test_eval_pulse3(self):
        # Test evaluating the entries of a pulse when everything is ok.
        # Start/Stop mode, meaningless stop (0).
        self.pulse.def_1 = '1.0*2.0'
        self.pulse.def_2 = '5.0*{a}/{b} + {c}'

        root_vars = {'a': 0.0, 'b': 10.0, 'c': 0.0}
        missing = set()
        errors = {}

        seq_locals = root_vars.copy()
        assert_false(self.pulse.eval_entries(root_vars, seq_locals,
                                             missing, errors))

        assert_equal(missing, set())
        assert_in('0_stop', errors)
        assert_not_in('0_stop', root_vars)
        assert_not_in('0_duration', root_vars)
        assert_not_in('0_stop', seq_locals)
        assert_not_in('0_duration', seq_locals)

    def test_eval_pulse4(self):
        # Test evaluating the entries of a pulse when everything is ok.
        # Start/Stop mode, meaningless stop < start.
        self.pulse.def_1 = '1.0*2.0'
        self.pulse.def_2 = '5.0*{a}/{b} + {c}'

        root_vars = {'a': 0.0, 'b': 10.0, 'c': 1.0}
        missing = set()
        errors = {}

        seq_locals = root_vars.copy()
        assert_false(self.pulse.eval_entries(root_vars, seq_locals,
                                             missing, errors))

        assert_equal(missing, set())
        assert_in('0_stop', errors)
        assert_not_in('0_stop', root_vars)
        assert_not_in('0_duration', root_vars)
        assert_not_in('0_stop', seq_locals)
        assert_not_in('0_duration', seq_locals)

    def test_eval_pulse5(self):
        # Test evaluating the entries of a pulse when everything is ok.
        # Start/Duration mode, meaningful values.
        self.pulse.def_mode = 'Start/Duration'
        self.pulse.def_1 = '1.0*2.0'
        self.pulse.def_2 = '5.0*{a}/{b} + {c}'

        root_vars = {'a': 2.0, 'b': 5.0, 'c': 1.0}
        missing = set()
        errors = {}

        seq_locals = root_vars.copy()
        assert_true(self.pulse.eval_entries(root_vars, seq_locals,
                                            missing, errors))

        assert_equal(missing, set())
        assert_equal(errors, {})
        assert_equal(root_vars['0_start'], 2.0)
        assert_equal(root_vars['0_stop'], 5.0)
        assert_equal(root_vars['0_duration'], 3.0)
        assert_equal(seq_locals['0_start'], 2.0)
        assert_equal(seq_locals['0_stop'], 5.0)
        assert_equal(seq_locals['0_duration'], 3.0)
        assert_equal(self.pulse.start, 2.0)
        assert_equal(self.pulse.stop, 5.0)
        assert_equal(self.pulse.duration, 3.0)
        assert_array_equal(self.pulse.waveform, np.ones(3))

    def test_eval_pulse6(self):
        # Test evaluating the entries of a pulse when everything is ok.
        # Start/Duration mode, meaningless start.
        self.pulse.def_mode = 'Start/Duration'
        self.pulse.def_1 = '-1.0*2.0'
        self.pulse.def_2 = '5.0*{a}/{b} + {c}'

        root_vars = {'a': 0.0, 'b': 10.0, 'c': 1.0}
        missing = set()
        errors = {}

        seq_locals = root_vars.copy()
        assert_false(self.pulse.eval_entries(root_vars, seq_locals,
                                             missing, errors))

        assert_equal(missing, set())
        assert_in('0_start', errors)
        assert_not_in('0_start', root_vars)
        assert_not_in('0_stop', root_vars)
        assert_not_in('0_start', seq_locals)
        assert_not_in('0_stop', seq_locals)

    def test_eval_pulse7(self):
        # Test evaluating the entries of a pulse when everything is ok.
        # Start/Duration mode, meaningless duration.
        self.pulse.def_mode = 'Start/Duration'
        self.pulse.def_1 = '1.0*2.0'
        self.pulse.def_2 = '5.0*{a}/{b} + {c}'

        root_vars = {'a': 0.0, 'b': 10.0, 'c': 0.0}
        missing = set()
        errors = {}

        seq_locals = root_vars.copy()
        assert_false(self.pulse.eval_entries(root_vars, seq_locals,
                                             missing, errors))

        assert_equal(missing, set())
        assert_in('0_duration', errors)
        assert_not_in('0_duration', root_vars)
        assert_not_in('0_stop', root_vars)
        assert_not_in('0_duration', seq_locals)
        assert_not_in('0_stop', seq_locals)

    def test_eval_pulse8(self):
        # Test evaluating the entries of a pulse when everything is ok.
        # Duration/Stop mode, meaningful values.
        self.pulse.def_mode = 'Duration/Stop'
        self.pulse.def_1 = '1.0*2.0'
        self.pulse.def_2 = '5.0*{a}/{b} + {c}'

        root_vars = {'a': 2.0, 'b': 5.0, 'c': 1.0}
        missing = set()
        errors = {}

        seq_locals = root_vars.copy()
        assert_true(self.pulse.eval_entries(root_vars, seq_locals,
                                            missing, errors))

        assert_equal(missing, set())
        assert_equal(errors, {})
        assert_equal(root_vars['0_start'], 1.0)
        assert_equal(root_vars['0_stop'], 3.0)
        assert_equal(root_vars['0_duration'], 2.0)
        assert_equal(seq_locals['0_start'], 1.0)
        assert_equal(seq_locals['0_stop'], 3.0)
        assert_equal(seq_locals['0_duration'], 2.0)
        assert_equal(self.pulse.start, 1.0)
        assert_equal(self.pulse.stop, 3.0)
        assert_equal(self.pulse.duration, 2.0)
        assert_array_equal(self.pulse.waveform, np.ones(2))

    def test_eval_pulse9(self):
        # Test evaluating the entries of a pulse Duration/Stop mode,
        # meaningless duration.
        self.pulse.def_mode = 'Duration/Stop'
        self.pulse.def_1 = '-1.0*2.0'
        self.pulse.def_2 = '5.0*{a}/{b} + {c}'

        root_vars = {'a': 0.0, 'b': 10.0, 'c': 1.0}
        missing = set()
        errors = {}

        seq_locals = root_vars.copy()
        assert_false(self.pulse.eval_entries(root_vars, seq_locals,
                                             missing, errors))

        assert_equal(missing, set())
        assert_in('0_duration', errors)
        assert_not_in('0_duration', root_vars)
        assert_not_in('0_start', root_vars)
        assert_not_in('0_duration', seq_locals)
        assert_not_in('0_start', seq_locals)

    def test_eval_pulse10(self):
        # Test evaluating the entries of a pulse Duration/Stop mode,
        # meaningless stop.
        self.pulse.def_mode = 'Duration/Stop'
        self.pulse.def_1 = '1.0*2.0'
        self.pulse.def_2 = '5.0*{a}/{b} + {c}'

        root_vars = {'a': 0.0, 'b': 10.0, 'c': 0.0}
        missing = set()
        errors = {}

        seq_locals = root_vars.copy()
        assert_false(self.pulse.eval_entries(root_vars, seq_locals,
                                             missing, errors))

        assert_equal(missing, set())
        assert_in('0_stop', errors)
        assert_not_in('0_stop', root_vars)
        assert_not_in('0_start', root_vars)
        assert_not_in('0_stop', seq_locals)
        assert_not_in('0_start', seq_locals)

    def test_eval_pulse11(self):
        # Test evaluating the entries of a pulse Duration/Stop mode, duration
        # larger than stop.
        self.pulse.def_mode = 'Duration/Stop'
        self.pulse.def_1 = '1.0*2.0'
        self.pulse.def_2 = '5.0*{a}/{b} + {c}'

        root_vars = {'a': 0.0, 'b': 10.0, 'c': 1.0}
        missing = set()
        errors = {}

        seq_locals = root_vars.copy()
        assert_false(self.pulse.eval_entries(root_vars, seq_locals,
                                             missing, errors))

        assert_equal(missing, set())
        assert_in('0_stop', errors)
        assert_not_in('0_start', root_vars)
        assert_not_in('0_start', seq_locals)

    def test_eval_pulse12(self):
        # Test evaluating the entries of a pulse when some vars are missing.
        # Issue in def_1
        self.pulse.def_1 = '1.0*2.0*{d}'
        self.pulse.def_2 = '5.0*{a}/{b} + {c}'

        root_vars = {'a': 2.0, 'b': 10.0, 'c': 1.0}
        missing = set()
        errors = {}

        seq_locals = root_vars.copy()
        assert_false(self.pulse.eval_entries(root_vars, seq_locals,
                                             missing, errors))

        assert_equal(missing, set('d'))
        assert_not_in('0_start', errors)
        assert_not_in('0_start', root_vars)
        assert_in('0_stop', root_vars)
        assert_not_in('0_start', seq_locals)
        assert_in('0_stop', seq_locals)

    def test_eval_pulse13(self):
        # Test evaluating the entries of a pulse when some vars are missing.
        # Issue in def_2
        self.pulse.def_1 = '1.0*2.0'
        self.pulse.def_2 = '5.0*{a}/{b} + {c}'

        root_vars = {'a': 2.0, 'b': 10.0}
        missing = set()
        errors = {}

        seq_locals = root_vars.copy()
        assert_false(self.pulse.eval_entries(root_vars, seq_locals,
                                             missing, errors))

        assert_equal(missing, set('c'))
        assert_not_in('0_stop', errors)
        assert_not_in('0_stop', root_vars)
        assert_in('0_start', root_vars)
        assert_not_in('0_stop', seq_locals)
        assert_in('0_start', seq_locals)

    def test_eval_pulse14(self):
        # Test evaluating the entries of a pulse when some entries are
        # incorrect.
        # Issue def_1
        self.pulse.def_1 = '1.0*2.0*zeffer'
        self.pulse.def_2 = '5.0*{a}/{b} + {c}'

        root_vars = {'a': 2.0, 'b': 10.0, 'c': 1.0}
        missing = set()
        errors = {}

        seq_locals = root_vars.copy()
        assert_false(self.pulse.eval_entries(root_vars, seq_locals,
                                             missing, errors))

        assert_equal(missing, set())
        assert_in('0_start', errors)
        assert_not_in('0_start', root_vars)
        assert_in('0_stop', root_vars)
        assert_not_in('0_start', seq_locals)
        assert_in('0_stop', seq_locals)

    def test_eval_pulse15(self):
        # Test evaluating the entries of a pulse when some entries are
        # incorrect.
        # Issue in def_2
        self.pulse.def_1 = '1.0*2.0'
        self.pulse.def_2 = '5.0*{a}/{b} + {c} + zeffer'

        root_vars = {'a': 2.0, 'b': 10.0, 'c': 1.0}
        missing = set()
        errors = {}

        seq_locals = root_vars.copy()
        assert_false(self.pulse.eval_entries(root_vars, seq_locals,
                                             missing, errors))

        assert_equal(missing, set())
        assert_in('0_stop', errors)
        assert_not_in('0_stop', root_vars)
        assert_in('0_start', root_vars)
        assert_not_in('0_stop', seq_locals)
        assert_in('0_start', seq_locals)

    def test_eval_pulse16(self):
        # Test evaluating the entries of an analogical pulse.
        self.pulse.def_1 = '1.0*2.0'
        self.pulse.def_2 = '5.0*{a}/{b} + {c}'

        self.pulse.shape = SquareShape(amplitude='0.5')
        self.pulse.kind = 'Analogical'

        root_vars = {'a': 2.0, 'b': 5.0, 'c': 1.0}
        missing = set()
        errors = {}

        assert_true(self.pulse.eval_entries(root_vars, root_vars,
                                            missing, errors))

        assert_equal(missing, set())
        assert_equal(errors, {})
        assert_array_equal(self.pulse.waveform, 0.5*np.ones(1))

    def test_eval_pulse17(self):
        # Test evaluating the entries of an analogical pulse whose modulation
        # evaluation fails.
        self.pulse.def_1 = '1.0*2.0'
        self.pulse.def_2 = '5.0*{a}/{b} + {c}'

        self.pulse.shape = SquareShape(amplitude='0.5')
        self.pulse.kind = 'Analogical'

        self.pulse.modulation.frequency = '1.0**'
        self.pulse.modulation.phase = '1.0'
        self.pulse.modulation.activated = True

        root_vars = {'a': 2.0, 'b': 5.0, 'c': 1.0}
        missing = set()
        errors = {}

        assert_false(self.pulse.eval_entries(root_vars, root_vars,
                                             missing, errors))

        assert_equal(missing, set())
        assert_in('0_mod_frequency', errors)

    def test_eval_pulse18(self):
        # Test evaluating the entries of an analogical pulse whose shape
        # evaluation fails.
        self.pulse.def_1 = '1.0*2.0'
        self.pulse.def_2 = '5.0*{a}/{b} + {c}'

        self.pulse.shape = SquareShape(amplitude='0.5*')
        self.pulse.kind = 'Analogical'

        self.pulse.modulation.frequency = '1.0'
        self.pulse.modulation.phase = '1.0'
        self.pulse.modulation.activated = True

        root_vars = {'a': 2.0, 'b': 5.0, 'c': 1.0}
        missing = set()
        errors = {}

        assert_false(self.pulse.eval_entries(root_vars, root_vars,
                                             missing, errors))

        assert_equal(missing, set())
        assert_in('0_shape_amplitude', errors)


class TestModulation(object):

    def test_eval_modulation1(self):
        # Test evaluating the entries of an inactive modulation.
        modulation = Modulation()
        root_vars = {'a': 1.0}
        missing = set()
        errors = {}

        assert_true(modulation.eval_entries(root_vars, missing, errors, 0))
        assert_equal(missing, set())
        assert_equal(errors, {})
        assert_array_equal(modulation.compute(np.zeros(1), 'mus'), 1.0)

    def test_eval_modulation2(self):
        # Test evaluating the entries of an active modulation.
        modulation = Modulation(activated=True)
        modulation.frequency = '1.0*{a}'
        modulation.phase = '0.0'

        root_vars = {'a': 1.0}
        missing = set()
        errors = {}

        assert_true(modulation.eval_entries(root_vars, missing, errors, 0))
        assert_equal(missing, set())
        assert_equal(errors, {})
        assert_array_equal(modulation.compute(np.array([0, 0.25]), 'mus'),
                           np.array([0, 1]))

    def test_eval_modulation3(self):
        # Test evaluating the entries of an active modulation when some vars
        # are missing.
        # Issue on frequency.
        modulation = Modulation(activated=True)
        modulation.frequency = '1.0*{a}'
        modulation.phase = '0.0'

        root_vars = {}
        missing = set()
        errors = {}

        assert_false(modulation.eval_entries(root_vars, missing, errors, 0))
        assert_equal(missing, set('a'))
        assert_in('0_mod_frequency', errors)

    def test_eval_modulation4(self):
        # Test evaluating the entries of an active modulation when some vars
        # are missing.
        # Issue on phase.
        modulation = Modulation(activated=True)
        modulation.frequency = '1.0'
        modulation.phase = '0.0*{a}'

        root_vars = {}
        missing = set()
        errors = {}

        assert_false(modulation.eval_entries(root_vars, missing, errors, 0))
        assert_equal(missing, set('a'))
        assert_in('0_mod_phase', errors)

    def test_eval_modulation5(self):
        # Test evaluating the entries of an active modulation when some entries
        # are incorrect.
        # Issue on frequency.
        modulation = Modulation(activated=True)
        modulation.frequency = '1.0*'
        modulation.phase = '0.0'

        root_vars = {}
        missing = set()
        errors = {}

        assert_false(modulation.eval_entries(root_vars, missing, errors, 0))
        assert_equal(missing, set())
        assert_in('0_mod_frequency', errors)

    def test_eval_modulation6(self):
        # Test evaluating the entries of an active modulation when some entries
        # are incorrect.
        # Issue on phase.
        modulation = Modulation(activated=True)
        modulation.frequency = '1.0'
        modulation.phase = '0.0*'

        root_vars = {}
        missing = set()
        errors = {}

        assert_false(modulation.eval_entries(root_vars, missing, errors, 0))
        assert_equal(missing, set())
        assert_in('0_mod_phase', errors)


class TestCompilation(object):

    def setup(self):
        self.root = RootSequence()
        self.context = TestContext(sampling=0.5)
        self.root.context = self.context

    def test_sequence_compilation1(self):
        # Test compiling a flat sequence.
        self.root.external_vars = {'a': 1.5}

        pulse1 = Pulse(def_1='1.0', def_2='{a}')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10')
        self.root.items.extend([pulse1, pulse2, pulse3])

        res, pulses = self.root.compile_sequence(False)
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

    def test_sequence_compilation1bis(self):
        # Compiles two times a sequence while changing a parameter to make
        # sure the cache is cleaned in between
        self.root.external_vars = {'a': 1.5}

        pulse1 = Pulse(def_1='1.0', def_2='{a}')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='4.0')
        pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10')
        self.root.items.extend([pulse1, pulse2, pulse3])

        res, pulses = self.root.compile_sequence(False)
        assert_true(res)
        assert_equal(len(pulses), 3)
        assert_equal(pulses[0].stop, 1.5)

        self.root.external_vars = {'a': 2.}
        res, pulses = self.root.compile_sequence(False)
        print res, pulses, pulse1.stop
        assert_true(res)
        assert_equal(len(pulses), 3)
        assert_equal(pulses[0].stop, 2.)


    def test_sequence_compilation2(self):
        # Test compiling a flat sequence of fixed duration.
        self.root.external_vars = {'a': 1.5}
        self.root.time_constrained = True
        self.root.sequence_duration = '10.0'

        pulse1 = Pulse(def_1='1.0', def_2='{a}')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='{sequence_end}')
        self.root.items.extend([pulse1, pulse2, pulse3])

        res, pulses = self.root.compile_sequence(False)
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

    def test_sequence_compilation3(self):
        # Test compiling a flat sequence in two passes.
        self.root.external_vars = {'a': 1.5}

        pulse1 = Pulse(def_1='1.0', def_2='{2_start} - 1.0')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10')
        self.root.items.extend([pulse1, pulse2, pulse3])

        res, pulses = self.root.compile_sequence(False)
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

    def test_sequence_compilation4(self):
        # Test compiling a flat sequence with circular references.
        self.root.external_vars = {'a': 1.5}

        pulse1 = Pulse(def_1='1.0', def_2='{2_start} - 1.0')
        pulse2 = Pulse(def_1='{1_stop} + 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10')
        self.root.items.extend([pulse1, pulse2, pulse3])

        res, (missings, errors) = self.root.compile_sequence(False)
        assert_false(res)
        assert_equal(len(missings), 2)
        assert_in('1_stop', missings)
        assert_in('2_start', missings)
        assert_equal(len(errors), 0)

    def test_sequence_compilation5(self):
        # Test compiling a flat sequence with evaluation errors.
        # missing global
        self.root.time_constrained = True
        self.root.sequence_duration = '10.0'

        pulse1 = Pulse(def_1='1.0', def_2='{a}')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='{sequence_end}')
        self.root.items.extend([pulse1, pulse2, pulse3])

        res, (missings, errors) = self.root.compile_sequence(False)
        assert_false(res)
        assert_equal(len(missings), 1)
        assert_in('a', missings)
        assert_equal(len(errors), 0)

    def test_sequence_compilation6(self):
        # Test compiling a flat sequence with evaluation errors.
        # wrong string value
        self.root.external_vars = {'a': 1.5}
        self.root.time_constrained = True
        self.root.sequence_duration = '*10.0*'

        pulse1 = Pulse(def_1='1.0', def_2='{a}')
        pulse2 = Pulse(def_1='{a} +* 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10.0')
        self.root.items.extend([pulse1, pulse2, pulse3])

        res, (missings, errors) = self.root.compile_sequence(False)
        assert_false(res)
        assert_false(missings)
        assert_equal(len(errors), 2)
        assert_in('2_start', errors)
        assert_in('root_seq_duration', errors)

    def test_sequence_compilation7(self):
        # Test compiling a nested sequence.
        self.root.external_vars = {'a': 1.5}

        pulse1 = Pulse(def_1='1.0', def_2='{a}')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{3_stop} + 0.5', def_2='10.0')
        pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
        pulse5 = Pulse(def_1='3.0', def_2='0.5', def_mode='Start/Duration')

        sequence2 = Sequence(items=[pulse3])
        sequence1 = Sequence(items=[pulse2, sequence2, pulse4])

        self.root.items = [pulse1, sequence1, pulse5]

        res, pulses = self.root.compile_sequence(False)
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

    def test_sequence_compilation8(self):
        # Test compiling a nested sequence in two passes on the external
        # sequence.
        self.root.external_vars = {'a': 1.5}

        pulse1 = Pulse(def_1='1.0', def_2='{7_start} - 1.0')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{3_stop} + 0.5', def_2='10.0')
        pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
        pulse5 = Pulse(def_1='3.0', def_2='0.5', def_mode='Start/Duration')

        sequence2 = Sequence(items=[pulse3])
        sequence1 = Sequence(items=[pulse2, sequence2, pulse4])

        self.root.items = [pulse1, sequence1, pulse5]

        res, pulses = self.root.compile_sequence(False)
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

    def test_sequence_compilation9(self):
        # Test compiling a nested sequence in multi passes.
        self.root.external_vars = {'a': 1.5}

        pulse1 = Pulse(def_1='1.0', def_2='{7_start} - 1.0')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='{6_start} + 1.0')
        pulse3 = Pulse(def_1='{3_stop} + 0.5', def_2='10.0')
        pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
        pulse5 = Pulse(def_1='3.0', def_2='0.5', def_mode='Start/Duration')

        sequence2 = Sequence(items=[pulse3])
        sequence1 = Sequence(items=[pulse2, sequence2, pulse4])

        self.root.items = [pulse1, sequence1, pulse5]

        res, pulses = self.root.compile_sequence(False)
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

    def test_sequence_compilation10(self):
        # Test compiling a nested sequence with circular reference in the deep
        # one.
        self.root.external_vars = {'a': 1.5}

        pulse1 = Pulse(def_1='1.0', def_2='{7_start} - 1.0')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='{6_start} + 1.0')
        pulse3 = Pulse(def_1='{3_stop} + 0.5', def_2='10.0')
        pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
        pulse5 = Pulse(def_1='{1_stop}', def_2='0.5',
                       def_mode='Start/Duration')

        sequence2 = Sequence(items=[pulse3])
        sequence1 = Sequence(items=[pulse2, sequence2, pulse4])

        self.root.items = [pulse1, sequence1, pulse5]

        res, (missings, errors) = self.root.compile_sequence(False)
        assert_false(res)
        assert_equal(len(missings), 2)
        assert_in('7_start', missings)
        assert_in('1_stop', missings)
        assert_false(errors)

    def test_sequence_compilation11(self):
        # Test compiling a nested sequence with circular reference in the deep
        # one.
        self.root.external_vars = {'a': 1.5}

        pulse1 = Pulse(def_1='1.0', def_2='{7_start} - 1.0')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='{6_start} + 1.0')
        pulse3 = Pulse(def_1='{3_stop} + *0.5', def_2='10.0')
        pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
        pulse5 = Pulse(def_1='3.0', def_2='0.5', def_mode='Start/Duration')

        sequence2 = Sequence(items=[pulse3])
        sequence1 = Sequence(items=[pulse2, sequence2, pulse4])

        self.root.items = [pulse1, sequence1, pulse5]

        res, (missings, errors) = self.root.compile_sequence(False)
        assert_false(res)
        assert_equal(len(errors), 1)
        assert_in('5_start', errors)

    def test_sequence_compilation12(self):
        # Test compiling a nested sequence using local vars.
        self.root.external_vars = {'a': 1.5}

        pulse1 = Pulse(def_1='1.0', def_2='{a}')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{3_stop} + 0.5', def_2='{b}')
        pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
        pulse5 = Pulse(def_1='3.0', def_2='0.5', def_mode='Start/Duration')

        sequence2 = Sequence(items=[pulse3], local_vars={'b': '2**2'})
        sequence1 = Sequence(items=[pulse2, sequence2, pulse4])

        self.root.items = [pulse1, sequence1, pulse5]

        res, pulses = self.root.compile_sequence(False)
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
        assert_equal(pulses[2].stop, 4)
        assert_equal(pulses[2].duration, 0.5)
        assert_is(pulses[3], pulse4)
        assert_equal(pulses[3].start, 2.0)
        assert_equal(pulses[3].stop, 2.5)
        assert_equal(pulses[3].duration, 0.5)
        assert_is(pulses[4], pulse5)
        assert_equal(pulses[4].start, 3.0)
        assert_equal(pulses[4].stop, 3.5)
        assert_equal(pulses[4].duration, 0.5)

    def test_sequence_compilation13(self):
        # Test compiling a nested sequence with wrong local vars definitions.
        self.root.external_vars = {'a': 1.5}

        pulse1 = Pulse(def_1='1.0', def_2='{a}')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{3_stop} + 0.5', def_2='{b}')
        pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
        pulse5 = Pulse(def_1='3.0', def_2='0.5', def_mode='Start/Duration')

        sequence2 = Sequence(items=[pulse3], local_vars={'b': '2**2*'})
        sequence1 = Sequence(items=[pulse2, sequence2, pulse4])

        self.root.items = [pulse1, sequence1, pulse5]

        res, (missings, errors) = self.root.compile_sequence(False)
        assert_false(res)
        assert_equal(len(missings), 1)
        assert_in('b', missings)
        assert_in('4_b', errors)

    def test_sequence_compilation14(self):
        # Test the locality of local vars.
        self.root.external_vars = {'a': 1.5}

        pulse1 = Pulse(def_1='1.0', def_2='{a}')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{3_stop} + 0.5', def_2='{b}')
        pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
        pulse5 = Pulse(def_1='3.0', def_2='{b}', def_mode='Start/Duration')

        sequence2 = Sequence(items=[pulse3], local_vars={'b': '2**2'})
        sequence1 = Sequence(items=[pulse2, sequence2, pulse4])

        self.root.items = [pulse1, sequence1, pulse5]

        res, (missings, errors) = self.root.compile_sequence(False)
        assert_false(res)
        assert_equal(len(missings), 1)
        assert_in('b', missings)
        assert_false(errors)

    # Here I don't test the evaluation errors on the defs as this is handled
    # at the Item level and tested in TestPulse.

    def test_sequence_compilation15(self):
        # Test compiling a nested sequence with internal fixed length.
        self.root.external_vars = {'a': 1.5}

        pulse1 = Pulse(def_1='1.0', def_2='{a}')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{4_start} + 0.5',
                       def_2='{4_start}+{4_duration}-0.5')
        pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
        pulse5 = Pulse(def_1='3.0', def_2='0.5', def_mode='Start/Duration')

        sequence2 = Sequence(items=[pulse3], time_constrained=True,
                             def_1='{3_stop} + 0.5', def_2='6')
        sequence1 = Sequence(items=[pulse2, sequence2, pulse4])

        self.root.items = [pulse1, sequence1, pulse5]

        res, pulses = self.root.compile_sequence(False)
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
        assert_equal(pulses[2].start, 4)
        assert_equal(pulses[2].stop, 5.5)
        assert_equal(pulses[2].duration, 1.5)
        assert_is(pulses[3], pulse4)
        assert_equal(pulses[3].start, 2.0)
        assert_equal(pulses[3].stop, 2.5)
        assert_equal(pulses[3].duration, 0.5)
        assert_is(pulses[4], pulse5)
        assert_equal(pulses[4].start, 3.0)
        assert_equal(pulses[4].stop, 3.5)
        assert_equal(pulses[4].duration, 0.5)

    def test_sequence_compilation16(self):
        # Test compiling a nested sequence with internal fixed length but
        # incoherent pulse start.
        self.root.external_vars = {'a': 1.5}

        pulse1 = Pulse(def_1='1.0', def_2='{a}')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{4_start} - 0.5',
                       def_2='{4_start}+{4_duration}-0.5')
        pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
        pulse5 = Pulse(def_1='3.0', def_2='0.5', def_mode='Start/Duration')

        sequence2 = Sequence(items=[pulse3], time_constrained=True,
                             def_1='{3_stop} + 0.5', def_2='6',
                             name='test')
        sequence1 = Sequence(items=[pulse2, sequence2, pulse4])

        self.root.items = [pulse1, sequence1, pulse5]

        res, (missings, errors) = self.root.compile_sequence(False)
        assert_false(res)
        assert_false(missings)
        assert_in('test-start', errors)

    def test_sequence_compilation17(self):
        # Test compiling a nested sequence with internal fixed length but
        # incoherent pulse stop.
        self.root.external_vars = {'a': 1.5}

        pulse1 = Pulse(def_1='1.0', def_2='{a}')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{4_start} + 0.5',
                       def_2='{4_start}+{4_duration}+0.5')
        pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
        pulse5 = Pulse(def_1='3.0', def_2='0.5', def_mode='Start/Duration')

        sequence2 = Sequence(items=[pulse3], time_constrained=True,
                             def_1='{3_stop} + 0.5', def_2='6',
                             name='test')
        sequence1 = Sequence(items=[pulse2, sequence2, pulse4])

        self.root.items = [pulse1, sequence1, pulse5]

        res, (missings, errors) = self.root.compile_sequence(False)
        assert_false(res)
        assert_false(missings)
        assert_in('test-stop', errors)

    def test_conditional_sequence_compilation1(self):
        # Test compiling a conditional sequence whose condition evaluates to
        # False.
        self.root.external_vars = {'a': 1.5, 'include': True}

        pulse1 = Pulse(def_1='1.0', def_2='{7_start} - 1.0')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{3_stop} + 0.5', def_2='10.0')
        pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
        pulse5 = Pulse(def_1='3.0', def_2='0.5', def_mode='Start/Duration')

        sequence2 = Sequence(items=[pulse3])
        sequence1 = ConditionalSequence(items=[pulse2, sequence2, pulse4],
                                        condition='{include}')

        self.root.items = [pulse1, sequence1, pulse5]

        res, pulses = self.root.compile_sequence(False)
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

    def test_conditional_sequence_compilation2(self):
        # Test compiling a conditional sequence whose condition evaluates to
        # True.
        self.root.external_vars = {'a': 1.5, 'include': False}

        pulse1 = Pulse(def_1='1.0', def_2='{7_start} - 1.0')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{3_stop} + 0.5', def_2='10.0')
        pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
        pulse5 = Pulse(def_1='3.0', def_2='0.5', def_mode='Start/Duration')

        sequence2 = Sequence(items=[pulse3])
        sequence1 = ConditionalSequence(items=[pulse2, sequence2, pulse4],
                                        condition='{include}')

        self.root.items = [pulse1, sequence1, pulse5]

        res, pulses = self.root.compile_sequence(False)
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

    def test_conditional_sequence_compilation3(self):
        # Test compiling a conditional sequence with a wrong condition.
        self.root.external_vars = {'a': 1.5, 'include': False}

        pulse1 = Pulse(def_1='1.0', def_2='{7_start} - 1.0')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{3_stop} + 0.5', def_2='10.0')
        pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
        pulse5 = Pulse(def_1='3.0', def_2='0.5', def_mode='Start/Duration')

        sequence2 = Sequence(items=[pulse3])
        sequence1 = ConditionalSequence(items=[pulse2, sequence2, pulse4],
                                        condition='{include}*/')

        self.root.items = [pulse1, sequence1, pulse5]

        res, (missings, errors) = self.root.compile_sequence(False)
        assert_false(res)
        assert_in('2_condition', errors)
