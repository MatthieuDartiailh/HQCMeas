# -*- coding: utf-8 -*-
# =============================================================================
# module : test_template_sequence.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
import os
from configobj import ConfigObj
from copy import deepcopy
from nose.tools import (assert_equal, assert_is, assert_true, assert_false,
                        assert_not_in, assert_in, assert_items_equal)
from hqc_meas.pulses.pulse import Pulse
from hqc_meas.pulses.base_sequences import RootSequence, Sequence
from hqc_meas.pulses.shapes.base_shapes import SquareShape
from hqc_meas.pulses.contexts.template_context import TemplateContext
from hqc_meas.pulses.sequences.template_sequence import TemplateSequence

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
    del pref['item_class']
    del pref['external_vars']
    del pref['time_constrained']
    return pref


class TestBuilding(object):

    def setup(self):
        pref = create_template_sequence()
        conf = ConfigObj()
        conf.update(pref)
        dep = {'Sequence': Sequence, 'Pulse': Pulse,
               'TemplateSequence': TemplateSequence,
               'shapes': {'SquareShape': SquareShape},
               'contexts': {'TemplateContext': TemplateContext,
                            'TestContext': TestContext},
               'templates': {'test': ('', conf, 'Basic user comment\nff')}}
        self.dependecies = {'pulses': dep}

    def test_build_from_config1(self):
        # Test building a template sequence from only the template file.
        # No information is knwon about channel mapping of template_vars values
        seq = TemplateSequence.build_from_config({'template_id': 'test',
                                                  'name': 'Template'},
                                                 self.dependecies)

        assert_equal(seq.name, 'Template')
        assert_equal(seq.template_id, 'test')
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

    def test_build_from_config2(self):
        # Test rebuilding a sequence including a template sequence.
        # Channel mapping of template_vars values are known.
        dep = deepcopy(self.dependecies)
        seq = TemplateSequence.build_from_config({'template_id': 'test',
                                                  'name': 'Template'},
                                                 dep)
        seq.template_vars = {'b': 25}
        seq.context.channel_mapping = {'A': 'Ch1_L', 'B': 'Ch2_L',
                                       'Ch1': 'Ch2_A', 'Ch2': 'Ch1_A'}
        root = RootSequence()
        context = TestContext(sampling=0.5)
        root.context = context
        root.items = [seq]
        pref = root.preferences_from_members()

        new = RootSequence.build_from_config(pref, self.dependecies)
        assert_equal(new.items[0].index, 1)

        assert_equal(seq.name, 'Template')
        assert_equal(seq.template_id, 'test')
        assert_equal(seq.template_vars, dict(b=25))
        assert_equal(seq.local_vars, dict(a=1.5))
        assert_equal(len(seq.items), 4)
        assert_equal(seq.items[3].index, 5)
        assert_equal(seq.docs, 'Basic user comment\nff')

        context = seq.context
        assert_equal(context.template, seq)
        assert_equal(context.logical_channels, ['A', 'B'])
        assert_equal(context.analogical_channels, ['Ch1', 'Ch2'])
        assert_equal(context.channel_mapping, {'A': 'Ch1_L', 'B': 'Ch2_L',
                                               'Ch1': 'Ch2_A', 'Ch2': 'Ch1_A'})


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