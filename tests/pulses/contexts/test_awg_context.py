# -*- coding: utf-8 -*-
# =============================================================================
# module : test_awg_context.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
import numpy as np
from nose.tools import (assert_equal, assert_true, assert_sequence_equal,
                        assert_in, assert_false)

from hqc_meas.pulses.contexts.awg_context import AWGContext
from hqc_meas.pulses.base_sequences import RootSequence, Sequence
from hqc_meas.pulses.pulse import Pulse
from hqc_meas.pulses.shapes.base_shapes import SquareShape
from hqc_meas.pulses.shapes.modulation import Modulation


class TestAWGContext(object):
    """
    """

    def setup(self):
        self.root = RootSequence()
        self.context = AWGContext()
        self.root.context = self.context

    def test_compiling_A_pulse(self):
        self.root.fix_sequence_duration = True
        self.root.sequence_duration = '1'
        pulse = Pulse(kind='analogical', shape=SquareShape(amplitude='1.0'),
                      def_1='0.1', def_2='0.5', channel='Ch1_A')
        self.root.items = [pulse]

        res, arrays = self.root.compile_sequence()
        assert_true(res)
        assert_in('Ch1', arrays)
        assert_equal(len(arrays), 1)

        sequence = np.zeros(2000, dtype=np.uint8)
        sequence[1::2] = 2**7 + 2**5
        sequence[201:1001:2] += 2**4 + 2**3 + 4 + 2 + 1
        sequence[200:1000:2] += 255
        assert_sequence_equal(arrays['Ch1'],
                              bytearray(sequence))

    def test_compiling_M1_pulse(self):
        self.root.fix_sequence_duration = True
        self.root.sequence_duration = '1'
        pulse = Pulse(kind='logical', def_1='0.1', def_2='0.5',
                      channel='Ch1_M1')
        self.root.items = [pulse]

        res, arrays = self.root.compile_sequence()
        assert_true(res)
        assert_in('Ch1', arrays)

        sequence = np.zeros(2000, dtype=np.uint8)
        sequence[1::2] = 2**7 + 2**5
        sequence[201:1001:2] += 2**6
        assert_sequence_equal(arrays['Ch1'],
                              bytearray(sequence))

    def test_compiling_M2_pulse(self):
        self.root.fix_sequence_duration = True
        self.root.sequence_duration = '1'
        pulse = Pulse(kind='logical', def_1='0.1', def_2='0.5',
                      channel='Ch1_M2')
        self.root.items = [pulse]

        res, arrays = self.root.compile_sequence()
        assert_true(res)
        assert_in('Ch1', arrays)

        sequence = np.zeros(2000, dtype=np.uint8)
        sequence[1::2] = 2**7 + 2**5
        sequence[201:1001:2] -= 2**7
        assert_sequence_equal(arrays['Ch1'],
                              bytearray(sequence))

    def test_compiling_variable_length(self):
        pulse = Pulse(kind='logical', def_1='0.1', def_2='0.5',
                      channel='Ch1_M1')
        self.root.items = [pulse]

        res, arrays = self.root.compile_sequence()
        assert_true(res)
        assert_in('Ch1', arrays)

        sequence = np.zeros(1000, dtype=np.uint8)
        sequence[1::2] = 2**7 + 2**5
        sequence[201:1001:2] += 2**6
        assert_sequence_equal(arrays['Ch1'],
                              bytearray(sequence))

    def test_too_short_fixed_length(self):
        self.root.fix_sequence_duration = True
        self.root.sequence_duration = '0.3'
        pulse = Pulse(kind='logical', def_1='0.1', def_2='0.5',
                      channel='Ch1_M1')
        self.root.items = [pulse]

        res, traceback = self.root.compile_sequence()
        assert_false(res)

    def test_channel_kind_mixing(self):
        self.root.fix_sequence_duration = True
        self.root.sequence_duration = '0.3'
        pulse = Pulse(kind='logical', def_1='0.1', def_2='0.5',
                      channel='Ch1_A')
        self.root.items = [pulse]

        res, traceback = self.root.compile_sequence()
        assert_false(res)

    def test_overlapping_pulses(self):
        self.root.fix_sequence_duration = True
        self.root.sequence_duration = '1'
        pulse1 = Pulse(kind='analogical', def_1='0.1', def_2='0.5',
                       channel='Ch1_A', shape=SquareShape(amplitude='1.0'),
                       modulation=Modulation(frequency='2.5', kind='sin',
                                             activated=True))
        pulse2 = Pulse(kind='analogical', def_1='0.1', def_2='0.5',
                       channel='Ch1_A', shape=SquareShape(amplitude='1.0'),
                       modulation=Modulation(frequency='2.5', kind='sin',
                                             phase='Pi', activated=True))
        self.root.items = [pulse1, pulse2]

        res, arrays = self.root.compile_sequence()
        assert_true(res)
        assert_in('Ch1', arrays)

    def test_nearly_overlapping_M2(self):
        self.root.fix_sequence_duration = True
        self.root.sequence_duration = '1'
        pulse1 = Pulse(kind='logical', def_1='0.1', def_2='0.5',
                       channel='Ch1_M2')
        pulse2 = Pulse(kind='logical', def_1='0.5', def_2='0.6',
                       channel='Ch1_M2')
        self.root.items = [pulse1, pulse2]

        res, arrays = self.root.compile_sequence()
        assert_true(res)
        assert_in('Ch1', arrays)

        sequence = np.zeros(2000, dtype=np.uint8)
        sequence[1::2] = 2**7 + 2**5
        sequence[201:1201:2] -= 2**7
        assert_sequence_equal(arrays['Ch1'],
                              bytearray(sequence))

    def test_overflow_check_A(self):
        self.root.fix_sequence_duration = True
        self.root.sequence_duration = '1'
        pulse1 = Pulse(kind='analogical', def_1='0.1', def_2='0.5',
                       channel='Ch1_A', shape=SquareShape(amplitude='1.0'),
                       modulation=Modulation(frequency='2.5', kind='sin',
                                             activated=True))
        pulse2 = Pulse(kind='analogical', def_1='0.1', def_2='0.5',
                       channel='Ch1_A', shape=SquareShape(amplitude='1.0'),
                       modulation=Modulation(frequency='2.5', kind='sin',
                                             activated=True))
        self.root.items = [pulse1, pulse2]

        res, traceback = self.root.compile_sequence()
        assert_false(res)
        assert_in('Ch1_A', traceback)

    def test_overflow_check_M1(self):
        self.root.fix_sequence_duration = True
        self.root.sequence_duration = '1'
        pulse1 = Pulse(kind='logical', def_1='0.1', def_2='0.5',
                       channel='Ch1_M1')
        pulse2 = Pulse(kind='logical', def_1='0.1', def_2='0.5',
                       channel='Ch1_M1')
        self.root.items = [pulse1, pulse2]

        res, traceback = self.root.compile_sequence()
        assert_false(res)
        assert_in('Ch1_M1', traceback)

    def test_overflow_check_M2(self):
        self.root.fix_sequence_duration = True
        self.root.sequence_duration = '1'
        pulse1 = Pulse(kind='logical', def_1='0.1', def_2='0.5',
                       channel='Ch1_M2')
        pulse2 = Pulse(kind='logical', def_1='0.4', def_2='0.6',
                       channel='Ch1_M2')
        self.root.items = [pulse1, pulse2]

        res, traceback = self.root.compile_sequence()
        assert_false(res)
        assert_in('Ch1_M2', traceback)

    def test_compiling_sequence1(self):
        self.root.external_vars = {'a': 1.5}

        pulse1 = Pulse(channel='Ch1_M1', def_1='1.0', def_2='{7_start} - 1.0')
        pulse2 = Pulse(channel='Ch1_M2',
                       def_1='{a} + 1.0', def_2='{6_start} + 1.0')
        pulse3 = Pulse(channel='Ch2_M1', def_1='{3_stop} + 0.5', def_2='10.0')
        pulse4 = Pulse(channel='Ch2_M2',
                       def_1='2.0', def_2='0.5', def_mode='Start/Duration')
        pulse5 = Pulse(channel='Ch3_M1',
                       def_1='3.0', def_2='0.5', def_mode='Start/Duration')

        sequence2 = Sequence(items=[pulse3])
        sequence1 = Sequence(items=[pulse2, sequence2, pulse4])

        self.root.items = [pulse1, sequence1, pulse5]

        res, arrays = self.root.compile_sequence()
        assert_true(res)
        assert_equal(len(arrays), 3)
        assert_equal(sorted(arrays.keys()), sorted(['Ch1', 'Ch2', 'Ch3']))
