# -*- coding: utf-8 -*-
# =============================================================================
# module : tests/pulses/manager/test_plugin.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from enaml.workbench.api import Workbench
import enaml
import os
from configobj import ConfigObj
from nose.tools import (assert_equal, assert_not_is_instance, assert_true,
                        assert_false, assert_in, assert_not_in,
                        assert_items_equal)
from nose.plugins.attrib import attr
from nose.plugins.skip import SkipTest

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state.manifest import StateManifest
    from hqc_meas.utils.preferences.manifest import PreferencesManifest
    from hqc_meas.utils.dependencies.manifest import DependenciesManifest
    from hqc_meas.pulses.manager.manifest import PulsesManagerManifest

from ...util import complete_line, create_test_dir, remove_tree
from ..template_makers import create_template_sequence


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)

HQC_MEAS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                             'hqc_meas')


class Test(object):

    test_dir = ''

    @classmethod
    def setup_class(cls):
        print complete_line(__name__ +
                            ':{}.setup_class()'.format(cls.__name__), '-', 77)
        # Creating dummy directory for prefs (avoid prefs interferences).
        directory = os.path.dirname(__file__)

        # Creating dummy directory for prefs (avoid prefs interferences).
        cls.test_dir = os.path.join(directory, '_temps')
        create_test_dir(cls.test_dir)

        # Creating dummy default.ini file in utils.
        util_path = os.path.join(HQC_MEAS_PATH, 'utils/preferences')
        def_path = os.path.join(util_path, 'default.ini')
        if os.path.isfile(def_path):
            os.rename(def_path, os.path.join(util_path, '__default.ini'))

        # Making the preference manager look for info in test dir.
        default = ConfigObj(def_path)
        default['folder'] = cls.test_dir
        default['file'] = 'default_test.ini'
        default.write()

        # Creating contexts preferences.
        contexts_path = os.path.join(HQC_MEAS_PATH, 'pulses', 'contexts')
        contexts_api = set(('awg_context.py',))
        contexts_loading = [unicode('contexts.' + mod[:-3])
                            for mod in os.listdir(contexts_path)
                            if mod.endswith('.py') and mod not in contexts_api]

        # Creating sequences preferences.
        sequences_path = os.path.join(HQC_MEAS_PATH, 'pulses', 'sequences')
        sequences_api = set(('conditional_sequence.py',))
        sequences_loading = [unicode('sequences.' + mod[:-3])
                             for mod in os.listdir(sequences_path)
                             if mod.endswith('.py') and
                             mod not in sequences_api]

        # Creating shapes preferences.
        shapes_path = os.path.join(HQC_MEAS_PATH, 'pulses', 'shapes')
        shapes_api = set(('base_shapes.py',))
        shapes_loading = [unicode('shapes.' + mod[:-3])
                          for mod in os.listdir(shapes_path)
                          if mod.endswith('.py') and mod not in shapes_api]

        # Creating a false template.
        template_path = os.path.join(cls.test_dir, 'temp_templates')
        os.mkdir(template_path)
        conf = ConfigObj()
        conf.filename = os.path.join(template_path, 'test.ini')
        conf.update(create_template_sequence())
        conf.write()

        # Saving plugin preferences.
        man_conf = {'contexts_loading': repr(contexts_loading),
                    'sequences_loading': repr(sequences_loading),
                    'shapes_loading': repr(shapes_loading),
                    'templates_folders': repr([template_path])}

        conf = ConfigObj(os.path.join(cls.test_dir, 'default_test.ini'))
        conf[u'hqc_meas.pulses'] = {}
        conf[u'hqc_meas.pulses'].update(man_conf)
        conf.write()

    @classmethod
    def teardown_class(cls):
        print complete_line(__name__ +
                            ':{}.teardown_class()'.format(cls.__name__), '-',
                            77)
        # Removing pref files creating during tests.
        remove_tree(cls.test_dir)

        # Restoring default.ini file in utils
        util_path = os.path.join(HQC_MEAS_PATH, 'utils/preferences')
        def_path = os.path.join(util_path, 'default.ini')
        os.remove(def_path)

        aux = os.path.join(util_path, '__default.ini')
        if os.path.isfile(aux):
            os.rename(aux, def_path)

    def setup(self):

        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(DependenciesManifest())

    def teardown(self):
        self.workbench.unregister(u'hqc_meas.pulses')
        self.workbench.unregister(u'hqc_meas.dependencies')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_init(self):
        self.workbench.register(PulsesManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.pulses')

        assert_in('sequences.__init__', plugin.sequences_loading)
        assert_in('contexts.__init__', plugin.contexts_loading)
        assert_in('shapes.__init__', plugin.shapes_loading)
        assert_items_equal(plugin.sequences, ['Conditional sequence',
                                              'Sequence', 'Test'])
        assert_items_equal(plugin._sequences.keys(),
                           ['Conditional sequence',
                            'Pulse', 'Sequence', 'RootSequence'])
        assert_items_equal(plugin._template_sequences.keys(),
                           ['Test'])
        assert_equal(plugin.shapes, ['Square'])
        assert_equal(plugin.contexts, ['AWG'])

    def test_load_all(self):
        self.workbench.register(PulsesManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.pulses')
        plugin.contexts_loading = []
        plugin.shapes_loading = []
        plugin.sequences_loading = []

        if plugin.report():
            raise SkipTest(plugin.report())

    @attr('no_travis')
    def test_template_observation(self):
        self.workbench.register(PulsesManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.pulses')
        assert_in('Test',  plugin.sequences)
        template_path = os.path.join(self.test_dir, 'temp_templates')
        prof = ConfigObj(os.path.join(template_path, 'template.ini'))
        prof.write()
        from time import sleep
        sleep(0.1)
        assert_in('Test',  plugin.sequences)
        assert_in('Template',  plugin.sequences)
        os.remove(os.path.join(template_path, 'template.ini'))
        sleep(0.1)
        assert_in('Test',  plugin.sequences)
        assert_not_in('Template',  plugin.sequences)

    def test_context_request1(self):
        # Request using context name
        self.workbench.register(PulsesManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.pulses.contexts_request'
        contexts, miss = core.invoke_command(com,
                                             {'contexts': ['AWG', 'XXXX']},
                                             self)

        assert_equal(contexts.keys(), ['AWG'])
        assert_equal(len(contexts['AWG']), 2)
        assert_equal(miss, ['XXXX'])

    def test_context_request2(self):
        # Request using class name, no views
        self.workbench.register(PulsesManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.pulses.contexts_request'
        contexts, miss = core.invoke_command(com, {'contexts': ['AWGContext'],
                                                   'use_class_names': True,
                                                   'views': False},
                                             self)
        assert_equal(contexts.keys(), ['AWGContext'])
        assert_not_is_instance(contexts['AWGContext'], tuple)
        assert_equal(miss, [])

    def test_shape_request1(self):
        # Request using shape name
        self.workbench.register(PulsesManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.pulses.shapes_request'
        shapes, miss = core.invoke_command(com,
                                           {'shapes': ['Square', 'XXXX']},
                                           self)

        assert_equal(shapes.keys(), ['Square'])
        assert_equal(len(shapes['Square']), 2)
        assert_equal(miss, ['XXXX'])

    def test_shape_request2(self):
        # Request using class name, no views
        self.workbench.register(PulsesManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.pulses.shapes_request'
        shapes, miss = core.invoke_command(com, {'shapes': ['SquareShape'],
                                                 'use_class_names': True,
                                                 'views': False},
                                           self)
        assert_equal(shapes.keys(), ['SquareShape'])
        assert_not_is_instance(shapes['SquareShape'], tuple)
        assert_equal(miss, [])

    def test_sequence_request1(self):
        # Request using sequence name
        self.workbench.register(PulsesManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.pulses.sequences_request'
        kwargs = {'sequences': ['Conditional sequence', 'XXXX']}
        sequences, miss = core.invoke_command(com, kwargs, self)

        assert_equal(sequences.keys(), ['Conditional sequence'])
        assert_equal(len(sequences['Conditional sequence']), 2)
        assert_equal(miss, ['XXXX'])

    def test_sequence_request2(self):
        # Request using class name, no views
        self.workbench.register(PulsesManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.pulses.sequences_request'
        kwargs = {'sequences': ['ConditionalSequence'],
                  'use_class_names': True, 'views': False}
        sequences, miss = core.invoke_command(com, kwargs, self)

        assert_equal(sequences.keys(), ['ConditionalSequence'])
        assert_not_is_instance(sequences['ConditionalSequence'], tuple)
        assert_equal(miss, [])

    def test_config_request_build1(self):
        # Test requesting a config for a standard sequence.
        self.workbench.register(PulsesManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.pulses')

        conf, view = plugin.config_request('Conditional sequence')

        assert_equal(type(conf).__name__, 'SequenceConfig')
        conf.sequence_name = 'Test'
        assert_equal(conf.config_ready, True)
        sequence = conf.build_sequence()
        assert_equal(sequence.name, 'Test')

#    def test_config_request_build2(self):
#        # Test requesting a config for a template sequence.
#        self.workbench.register(PulsesManagerManifest())
#        core = self.workbench.get_plugin(u'enaml.workbench.core')
#        com = u'hqc_meas.task_manager.config_request'
#
#        conf, view = core.invoke_command(com, {'task': 'Template'}, self)
#        assert_equal(type(conf).__name__, 'IniConfigTask')
#        conf.task_name = 'Test'
#        assert_equal(conf.config_ready, True)
#        task = conf.build_task()
#        assert_equal(task.task_name, 'Test')
#        assert_equal(len(task.children_task), 1)
#        task2 = task.children_task[0]
#        assert_equal(task2.task_name, 'a')
#        assert_equal(task2.task_class, 'LogTask')

    def test_filter(self):
        # Filtering sequences.
        self.workbench.register(PulsesManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.pulses')

        seq = plugin.filter_sequences('All')
        assert_in('Sequence', seq)
        assert_not_in('Pulse', seq)
        assert_not_in('RootSequence', seq)

    def test_collect_dependencies(self):
        # Test collecting build dependencies.
        self.workbench.register(PulsesManagerManifest())
        from hqc_meas.pulses.base_sequences import RootSequence, Sequence
        from hqc_meas.pulses.pulse import Pulse
        from hqc_meas.pulses.shapes.base_shapes import SquareShape
        from hqc_meas.pulses.contexts.awg_context import AWGContext
        root = RootSequence(context=AWGContext())

        pulse1 = Pulse(def_1='1.0', def_2='{7_start} - 1.0')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='{6_start} + 1.0')
        pulse3 = Pulse(def_1='{3_stop} + 0.5', def_2='10.0')
        pulse4 = Pulse(def_1='2.0', def_2='0.5', def_mode='Start/Duration')
        pulse5 = Pulse(def_1='{1_stop}', def_2='0.5',
                       def_mode='Start/Duration')
        pulse5.shape = SquareShape(amplitude='0.5')
        pulse5.kind = 'Analogical'

        pulse5.modulation.frequency = '1.0**'
        pulse5.modulation.phase = '1.0'
        pulse5.modulation.activated = True

        sequence2 = Sequence(items=[pulse3])
        sequence1 = Sequence(items=[pulse2, sequence2, pulse4])

        root.items = [pulse1, sequence1, pulse5]

        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.dependencies.collect_dependencies'
        res, build, run = core.invoke_command(com, {'obj': root}, core)
        assert_true(res)
        assert_in('pulses', build)
        assert_items_equal(['Sequence', 'Pulse', 'RootSequence', 'shapes',
                            'contexts', 'templates', 'sequences'],
                           build['pulses'].keys())
        assert_equal(['SquareShape'], build['pulses']['shapes'].keys())
        assert_equal(['AWGContext'], build['pulses']['contexts'].keys())
        assert_false(run)

    def test_collect_dependencies2(self):
        # Test collecting_dependencies for a sequence including a template
        # sequence.
        self.workbench.register(PulsesManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.pulses')
        plugin.contexts_loading = []
        plugin.sequences_loading = []

        # TODO rr

    def test_collect_dependencies3(self):
        # Test collecting_dependencies for a walk containing a sequence path.
        self.workbench.register(PulsesManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.pulses')
        plugin.contexts_loading = []
        plugin.sequences_loading = []
