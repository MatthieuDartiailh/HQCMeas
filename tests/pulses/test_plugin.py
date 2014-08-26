# -*- coding: utf-8 -*-
from enaml.workbench.api import Workbench
import enaml
import os
import shutil
from configobj import ConfigObj
from nose.tools import assert_equal, assert_not_is_instance
from nose.plugins.skip import SkipTest

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state.manifest import StateManifest
    from hqc_meas.utils.preferences.manifest import PreferencesManifest
    from hqc_meas.pulses.manager.manifest import PulsesManagerManifest

from ..util import complete_line


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


class Test(object):

    test_dir = ''

    @classmethod
    def setup_class(cls):
        print complete_line(__name__ +
                            ':{}.setup_class()'.format(cls.__name__), '-', 77)
        # Creating dummy directory for prefs (avoid prefs interferences).
        directory = os.path.dirname(__file__)
        cls.test_dir = os.path.join(directory, '_temps')
        os.mkdir(cls.test_dir)

        # Creating dummy default.ini file in utils.
        util_path = os.path.join(directory, '..', '..', 'hqc_meas', 'utils')
        def_path = os.path.join(util_path, 'default.ini')
        if os.path.isfile(def_path):
            os.rename(def_path, os.path.join(util_path, '__default.ini'))

        # Making the preference manager look for info in test dir.
        default = ConfigObj(def_path)
        default['folder'] = cls.test_dir
        default['file'] = 'default_test.ini'
        default.write()

        # Creating contexts preferences.
        contexts_path = os.path.join(directory, '..', '..', 'hqc_meas',
                                     'pulses', 'contexts')
        contexts_api = set(('awg_context.py',))
        contexts_loading = [unicode('contexts.' + mod[:-3])
                            for mod in os.listdir(contexts_path)
                            if mod.endswith('.py') and mod not in contexts_api]

        # Creating sequences preferences.
        sequences_path = os.path.join(directory, '..', '..', 'hqc_meas',
                                      'pulses', 'sequences')
        sequences_api = set(('conditional_sequence.py',))
        sequences_loading = [unicode('sequences.' + mod[:-3])
                             for mod in os.listdir(sequences_path)
                             if mod.endswith('.py') and
                             mod not in sequences_api]

        # Creating shapes preferences.
        shapes_path = os.path.join(directory, '..', '..', 'hqc_meas', 'pulses',
                                   'shapes')
        shapes_api = set(('base_shapes.py',))
        shapes_loading = [unicode('shapes.' + mod[:-3])
                          for mod in os.listdir(shapes_path)
                          if mod.endswith('.py') and mod not in shapes_api]

        # Copying false template.
# TODO activate later when templates will be supported.
#        template_path = os.path.join(cls.test_dir, 'temp_templates')
#        os.mkdir(template_path)
#        # Not in the root test dirt otherwise .ini got deleted ...
#        # Not understood but unlinked to shutil.
#        shutil.copyfile(os.path.join(directory, 'config_files',
#                                     'template_ref.ini'),
#                        os.path.join(template_path, 'template.ini'))

        # Saving plugin preferences.
        man_conf = {'contexts_loading': repr(contexts_loading),
                    'sequences_loading': repr(sequences_loading),
                    'shapes_loading': repr(shapes_loading)}

        conf = ConfigObj(os.path.join(cls.test_dir, 'default_test.ini'))
        conf[u'hqc_meas.pulses_manager'] = {}
        conf[u'hqc_meas.pulses_manager'].update(man_conf)
        conf.write()

    @classmethod
    def teardown_class(cls):
        print complete_line(__name__ +
                            ':{}.teardown_class()'.format(cls.__name__), '-',
                            77)
        # Removing pref files creating during tests.
        try:
            shutil.rmtree(cls.test_dir)

        # Hack for win32.
        except OSError:
            print 'OSError'
            dirs = os.listdir(cls.test_dir)
            for directory in dirs:
                shutil.rmtree(os.path.join(cls.test_dir), directory)
            shutil.rmtree(cls.test_dir)

        # Restoring default.ini file in utils
        directory = os.path.dirname(__file__)
        util_path = os.path.join(directory, '..', '..', 'hqc_meas', 'utils')
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

    def teardown(self):
        self.workbench.unregister(u'hqc_meas.pulses_manager')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_init(self):
        self.workbench.register(PulsesManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.pulses_manager')

        assert_equal(sorted(plugin.sequences), sorted(['Conditional sequence',
                     'Pulse', 'Sequence', 'RootSequence']))
        assert_equal(plugin.shapes, ['Square'])
        assert_equal(plugin.contexts, ['AWG'])

    def test_load_all(self):
        self.workbench.register(PulsesManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.pulses_manager')
        plugin.contexts_loading = []
        plugin.shapes_loading = []
        plugin.sequences_loading = []

        if plugin.report():
            raise SkipTest(plugin.report())

#    def test_template_observation(self):
#        self.workbench.register(TaskManagerManifest())
#        plugin = self.workbench.get_plugin(u'hqc_meas.task_manager')
#        assert_in('Template',  plugin.tasks)
#        template_path = os.path.join(self.test_dir, 'temp_templates')
#        prof = ConfigObj(os.path.join(template_path, 'test.ini'))
#        prof.write()
#        from time import sleep
#        sleep(0.1)
#        assert_in('Test',  plugin.tasks)
#        assert_in('Template',  plugin.tasks)
#        os.remove(os.path.join(template_path, 'test.ini'))
#        sleep(0.1)
#        assert_not_in('Test',  plugin.tasks)
#        assert_in('Template',  plugin.tasks)

    def test_context_request1(self):
        # Request using context name
        self.workbench.register(PulsesManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.pulses_manager.contexts_request'
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
        com = u'hqc_meas.pulses_manager.contexts_request'
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
        com = u'hqc_meas.pulses_manager.shapes_request'
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
        com = u'hqc_meas.pulses_manager.shapes_request'
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
        com = u'hqc_meas.pulses_manager.sequences_request'
        kwargs = {'sequences': ['Conditional sequence', 'XXXX']}
        sequences, miss = core.invoke_command(com, kwargs, self)

        assert_equal(sequences.keys(), ['Conditional sequence'])
        assert_equal(len(sequences['Conditional sequence']), 2)
        assert_equal(miss, ['XXXX'])

    def test_sequence_request2(self):
        # Request using class name, no views
        self.workbench.register(PulsesManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.pulses_manager.sequences_request'
        kwargs = {'sequences': ['ConditionalSequence'],
                  'use_class_names': True, 'views': False}
        sequences, miss = core.invoke_command(com, kwargs, self)

        assert_equal(sequences.keys(), ['ConditionalSequence'])
        assert_not_is_instance(sequences['ConditionalSequence'], tuple)
        assert_equal(miss, [])
