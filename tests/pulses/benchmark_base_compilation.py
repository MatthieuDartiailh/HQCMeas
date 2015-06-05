# -*- coding: utf-8 -*-
# =============================================================================
# module : benchmark_base_pulses.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from functools import partial
from timeit import repeat


def time(*args, **kwargs):
    kwargs['number'] = 100
    kwargs['repeat'] = 100
    return min(repeat(*args, **kwargs))/kwargs['number']

from hqc_meas.pulses.base_sequences import RootSequence, Sequence
from hqc_meas.pulses.pulse import Pulse
from hqc_meas.pulses.sequences.conditional_sequence import ConditionalSequence
from hqc_meas.pulses.shapes.base_shapes import SquareShape
from hqc_meas.pulses.shapes.modulation import Modulation

from .context import TestContext


class BenchmarkCompilation(object):

    def setup(self):
        self.root = RootSequence()
        self.context = TestContext(sampling=0.5)
        self.root.context = self.context

    def benchmark_sequence_compilation1(self):
        # Test compiling a flat sequence.
        self.root.external_vars = {'a': 1.5}

        pulse1 = Pulse(def_1='1.0', def_2='{a}')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10')
        self.root.items.extend([pulse1, pulse2, pulse3])

        print 'Sequence 1', time(partial(self.root.compile_sequence, False))

    def benchmark_sequence_compilation2(self):
        # Test compiling a flat sequence of fixed duration.
        self.root.external_vars = {'a': 1.5}
        self.root.fix_sequence_duration = True
        self.root.sequence_duration = '10.0'

        pulse1 = Pulse(def_1='1.0', def_2='{a}')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='{sequence_end}')
        self.root.items.extend([pulse1, pulse2, pulse3])

        print 'Sequence 2', time(partial(self.root.compile_sequence, False))

    def benchmark_sequence_compilation3(self):
        # Test compiling a flat sequence in two passes.
        self.root.external_vars = {'a': 1.5}

        pulse1 = Pulse(def_1='1.0', def_2='{2_start} - 1.0')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
        pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10')
        self.root.items.extend([pulse1, pulse2, pulse3])

        print 'Sequence 3', time(partial(self.root.compile_sequence, False))

    def benchmark_sequence_compilation7(self):
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

        print 'Sequence 7', time(partial(self.root.compile_sequence, False))

    def benchmark_sequence_compilation8(self):
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

        print 'Sequence 8', time(partial(self.root.compile_sequence, False))

    def benchmark_sequence_compilation9(self):
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

        print 'Sequence 9', time(partial(self.root.compile_sequence, False))

    def benchmark_conditional_sequence_compilation1(self):
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

        print 'Conditional seq 1', time(partial(self.root.compile_sequence,
                                                False))

    def benchmark_conditional_sequence_compilation2(self):
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

        print 'Conditional seq 2', time(partial(self.root.compile_sequence,
                                                False))
