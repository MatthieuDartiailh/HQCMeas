# -*- coding: utf-8 -*-
# =============================================================================
# module : test_template_sequence.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
import os
from configobj import ConfigObj
from nose.tools import (assert_equal, assert_true, assert_false,
                        assert_in)
from hqc_meas.pulses.pulse import Pulse
from hqc_meas.pulses.base_sequences import RootSequence, Sequence
from hqc_meas.pulses.shapes.base_shapes import SquareShape
from hqc_meas.pulses.contexts.template_context import TemplateContext
from hqc_meas.pulses.sequences.template_sequence import TemplateSequence

from ..context import TestContext
from ..template_makers import create_template_sequence


PACKAGE_PATH = os.path.dirname(__file__)


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
        conf = {'template_id': 'test', 'name': 'Template',
                'template_vars': "{'b': '19', 'c': ''}"}
        seq = TemplateSequence.build_from_config(conf, self.dependecies)

        assert_equal(seq.name, 'Template')
        assert_equal(seq.template_id, 'test')
        assert_equal(seq.template_vars, dict(b='19'))
        assert_equal(seq.local_vars, dict(a='1.5'))
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
        conf = {'template_id': 'test', 'name': 'Template',
                'template_vars': "{'b': '25'}"}
        seq = TemplateSequence.build_from_config(conf, self.dependecies)
        seq.context.channel_mapping = {'A': 'Ch1_L', 'B': 'Ch2_L',
                                       'Ch1': 'Ch2_A', 'Ch2': 'Ch1_A'}
        root = RootSequence()
        context = TestContext(sampling=0.5)
        root.context = context
        root.items = [seq]
        pref = root.preferences_from_members()

        new = RootSequence.build_from_config(pref, self.dependecies)
        assert_equal(new.items[0].index, 1)

        seq = new.items[0]
        assert_equal(seq.name, 'Template')
        assert_equal(seq.template_id, 'test')
        assert_equal(seq.template_vars, dict(b='25'))
        assert_equal(seq.local_vars, dict(a='1.5'))
        assert_equal(len(seq.items), 4)
        assert_equal(seq.items[3].index, 5)
        assert_equal(seq.docs, 'Basic user comment\nff')

        context = seq.context
        assert_equal(context.template, seq)
        assert_equal(context.logical_channels, ['A', 'B'])
        assert_equal(context.analogical_channels, ['Ch1', 'Ch2'])
        assert_equal(context.channel_mapping, {'A': 'Ch1_L', 'B': 'Ch2_L',
                                               'Ch1': 'Ch2_A', 'Ch2': 'Ch1_A'})

    def test_build_from_config(self):
        # Test rebuilding a sequence including twice the same template sequence
        conf = {'template_id': 'test', 'name': 'Template',
                'template_vars': "{'b': '19'}"}
        seq = TemplateSequence.build_from_config(conf, self.dependecies)
        seq.context.channel_mapping = {'A': 'Ch1_L', 'B': 'Ch2_L',
                                       'Ch1': 'Ch2_A', 'Ch2': 'Ch1_A'}

        conf = {'template_id': 'test', 'name': 'Template',
                'template_vars': "{'b': '12'}"}
        seq2 = TemplateSequence.build_from_config(conf, self.dependecies)
        seq2.context.channel_mapping = {'A': 'Ch1_L', 'B': 'Ch2_L',
                                        'Ch1': 'Ch1_A', 'Ch2': 'Ch2_A'}

        root = RootSequence()
        context = TestContext(sampling=0.5)
        root.context = context
        root.items = [seq, seq2]
        pref = root.preferences_from_members()

        new = RootSequence.build_from_config(pref, self.dependecies)
        assert_equal(new.items[0].index, 1)

        seq = new.items[0]
        assert_equal(seq.name, 'Template')
        assert_equal(seq.template_id, 'test')
        assert_equal(seq.template_vars, dict(b='19'))
        assert_equal(seq.local_vars, dict(a='1.5'))
        assert_equal(len(seq.items), 4)
        assert_equal(seq.items[3].index, 5)
        assert_equal(seq.docs, 'Basic user comment\nff')

        context = seq.context
        assert_equal(context.template, seq)
        assert_equal(context.logical_channels, ['A', 'B'])
        assert_equal(context.analogical_channels, ['Ch1', 'Ch2'])
        assert_equal(context.channel_mapping, {'A': 'Ch1_L', 'B': 'Ch2_L',
                                               'Ch1': 'Ch2_A', 'Ch2': 'Ch1_A'})

        assert_equal(new.items[1].index, 2)

        seq = new.items[1]
        assert_equal(seq.name, 'Template')
        assert_equal(seq.template_id, 'test')
        assert_equal(seq.template_vars, dict(b='12'))
        assert_equal(seq.local_vars, dict(a='1.5'))
        assert_equal(len(seq.items), 4)
        assert_equal(seq.items[3].index, 5)
        assert_equal(seq.docs, 'Basic user comment\nff')

        context = seq.context
        assert_equal(context.template, seq)
        assert_equal(context.logical_channels, ['A', 'B'])
        assert_equal(context.analogical_channels, ['Ch1', 'Ch2'])
        assert_equal(context.channel_mapping, {'A': 'Ch1_L', 'B': 'Ch2_L',
                                               'Ch1': 'Ch1_A', 'Ch2': 'Ch2_A'})


class TestCompilation(object):

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

        self.root = RootSequence()
        self.context = TestContext(sampling=0.5)
        self.root.context = self.context

        conf = {'template_id': 'test', 'name': 'Template',
                'template_vars': "{'b': '19'}"}
        seq = TemplateSequence.build_from_config(conf, self.dependecies)
        seq.context.channel_mapping = {'A': 'Ch1_L', 'B': 'Ch2_L',
                                       'Ch1': 'Ch2_A', 'Ch2': 'Ch1_A'}
        seq.def_1 = '1.0'
        seq.def_2 = '20.0'

        self.template = seq

        self.root.items = [seq]

    def test_sequence_compilation1(self):
        # Test compiling a template when everything is ok.
        res, pulses = self.root.compile_sequence(False)

        assert_true(res, '{}'.format(pulses))
        assert_equal(len(pulses), 4)

        pulse = pulses[0]
        assert_equal(pulse.index, 1)
        assert_equal(pulse.start, 2.0)
        assert_equal(pulse.stop, 2.5)
        assert_equal(pulse.duration, 0.5)
        assert_equal(pulse.channel, 'Ch1_L')

        pulse = pulses[1]
        assert_equal(pulse.index, 2)
        assert_equal(pulse.start, 3.5)
        assert_equal(pulse.stop, 4)
        assert_equal(pulse.duration, 0.5)
        assert_equal(pulse.channel, 'Ch2_L')

        pulse = pulses[2]
        assert_equal(pulse.index, 4)
        assert_equal(pulse.start, 4.5)
        assert_equal(pulse.stop, 20)
        assert_equal(pulse.duration, 15.5)
        assert_equal(pulse.channel, 'Ch1_A')

        pulse = pulses[3]
        assert_equal(pulse.index, 5)
        assert_equal(pulse.start, 4.5)
        assert_equal(pulse.stop, 20)
        assert_equal(pulse.duration, 15.5)
        assert_equal(pulse.channel, 'Ch2_A')

    def test_sequence_compilation2(self):
        # Test compiling a template : issue in context, incomplete mapping.
        self.template.context.channel_mapping = {'A': 'Ch1_L', 'B': 'Ch2_L',
                                                 'Ch1': 'Ch2_A'}

        res, (miss, errors) = self.root.compile_sequence(False)

        assert_false(res)
        assert_false(miss)
        assert_in('Template-context', errors)
        assert_in('Ch2', errors['Template-context'])

    def test_sequence_compilation3(self):
        # Test compiling a template : issue in context, erroneous mapping.
        self.template.context.channel_mapping = {'A': 'Ch1_L', 'B': 'Ch2_L',
                                                 'Ch1': 'Ch2_A', 'Ch2': 'A'}

        res, (miss, errors) = self.root.compile_sequence(False)

        assert_false(res)
        assert_false(miss)
        assert_in('Template-context', errors)
        assert_in('Ch2', errors['Template-context'])

    def test_sequence_compilation3bis(self):
        # Test compiling a template : pulse as umapped channel.
        self.template.items[0].channel = '__'
        res, (miss, errors) = self.root.compile_sequence(False)

        assert_false(res)
        assert_false(miss)
        assert_in('Template-channels', errors)
        assert_in('__', errors['Template-channels'])

    def test_sequence_compilation4(self):
        # Test compiling a template : issue in defs.
        self.template.def_1 = 'r*'

        res, (miss, errors) = self.root.compile_sequence(False)

        assert_false(res)
        assert_false(miss)
        assert_in('1_start', errors)

    def test_sequence_compilation5(self):
        # Test compiling a template : issue in template_vars.
        self.template.template_vars = {'b': '*1'}

        res, (miss, errors) = self.root.compile_sequence(False)

        assert_false(res)
        assert_in('1_b', errors)

    def test_sequence_compilation6(self):
        # Test compiling a template : issue in local_vars.
        self.template.local_vars = {'a': '*1'}

        res, (miss, errors) = self.root.compile_sequence(False)

        assert_false(res)
        assert_in('1_a', errors)

    def test_sequence_compilation7(self):
        # Test compiling a template : issue in stop time.
        self.template.items[0].def_2 = '200'

        res, (miss, errors) = self.root.compile_sequence(False)

        assert_false(res)
        assert_in('Template-stop', errors)
