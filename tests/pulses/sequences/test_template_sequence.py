# -*- coding: utf-8 -*-
# =============================================================================
# module : test_template_sequence.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
import os
from configobj import ConfigObj
from nose.tools import (assert_equal, assert_is, assert_true, assert_false,
                        assert_not_in, assert_in, assert_items_equal)
from hqc_meas.pulses.pulse import Pulse
from hqc_meas.pulses.base_sequences import RootSequence, Sequence
from hqc_meas.pulses.shapes.base_shapes import SquareShape
from hqc_meas.pulses.contexts.template_context import TemplateContext
from hqc_meas.pulses.sequences.template_sequence import TemplateSequence

from ...util import create_test_dir, remove_tree
from ..context import TestContext


PACKAGE_PATH = os.path.dirname(__file__)


def create_template_sequence():
    root = RootSequence()
    context = TemplateContext(logical_channels=['A', 'B'],
                              analogical_channels=['Ch1', 'Ch2'],
                              channel_mapping={'A': '', 'B': '', 'Ch1': '',
                                               'Ch2': ''})
    root.context = context
    root.local_vars = {'a': 1.5}

    pulse1 = Pulse(def_1='1.0', def_2='{a}')
    pulse2 = Pulse(def_1='{a} + 1.0', def_2='3.0')
    pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='{b}',
                   kind='analogical', shape=SquareShape())
    seq = Sequence(items=[Pulse(def_1='{2_stop} + 0.5', def_2='10',
                                kind='analogical', shape=SquareShape())])
    root.items.extend([pulse1, pulse2, seq,  pulse3])

    pref = root.preferences_from_members()
    pref['template_vars'] = repr(dict(b=''))
    return pref


class TestBuilding(object):

    test_dir = ''

    @classmethod
    def setup_class(cls):
        test_dir = os.path.join(PACKAGE_PATH, 'tests')
        create_test_dir(test_dir)
        cls.test_dir = test_dir

        pref = create_template_sequence()
        conf = ConfigObj(os.path.join(test_dir, 'template.ini'))
        conf.update(pref)
        conf.initial_comment = 'Basic user comment\nff'
        conf.write()

    @classmethod
    def teardown_class(cls):
        remove_tree(cls.test_dir)

    def setup(self):
        dep = {'Sequence': Sequence, 'Pulse': Pulse,
               'shapes': {'SquareShape': SquareShape},
               'contexts': {'BaseContext': TemplateContext}}
        self.dependecies = {'pulses': dep}

    def test_build_from_config1(self):
        # Test building a template sequence from only the template file.
        t_path = os.path.join(self.test_dir, 'template.ini')
        seq = TemplateSequence.build_from_config({'template_path': t_path,
                                                  'name': 'Template'},
                                                 self.dependecies)

        assert_equal(seq.name, 'Template')
        assert_equal(seq.template_path, t_path)
        assert_equal(seq.template_vars, dict(b=''))
        assert_equal(seq.local_vars, dict(a=1.5))
        assert_equal(len(seq.items), 4)
        assert_equal(seq.items[3].index, 5)
        assert_equal(seq.docs, 'Basic user comment\nff')

        context = seq.context
        assert_equal(context.template, seq)
        assert_equal(context.logical_channels, ['A', 'B'])
        assert_equal(context.analogical_channels, ['Ch1', 'Ch2'])
        assert_equal(context.channel_mapping, {'A': '', 'B': '', 'Ch1': '',
                                               'Ch2': ''})

    def test_building_from_config2(self):
        # Test rebuilding a sequence including a template sequence.
        pass


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
        print pulses
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