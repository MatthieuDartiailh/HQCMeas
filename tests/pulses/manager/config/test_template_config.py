# =============================================================================
# module : tests/pulses/manager/config/test_base_config.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
import os
from ast import literal_eval
from nose.tools import (assert_items_equal, assert_equal, assert_is_instance,
                        assert_false, assert_true, assert_is)
from configobj import ConfigObj

from hqc_meas.pulses.api import RootSequence, Sequence
from hqc_meas.pulses.sequences.template_sequence import TemplateSequence
from hqc_meas.pulses.manager.config.template_config import TemplateConfig
from enaml.workbench.api import Workbench
import enaml

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state.manifest import StateManifest
    from hqc_meas.utils.preferences.manifest import PreferencesManifest
    from hqc_meas.utils.dependencies.manifest import DependenciesManifest
    from hqc_meas.pulses.manager.manifest import PulsesManagerManifest

from ....util import complete_line, create_test_dir, remove_tree
from ...sequences.test_template_sequence import create_template_sequence


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


FILE_DIR = os.path.dirname(__file__)
PACKAGE_PATH = os.path.join(FILE_DIR, '..', '..', '..', '..', 'hqc_meas')


class TestTemplateConfig(object):
    """
    """

    test_dir = ''

    @classmethod
    def setup_class(cls):
        print complete_line(__name__ +
                            ':{}.setup_class()'.format(cls.__name__), '-', 77)
        # Creating dummy directory for prefs (avoid prefs interferences).
        cls.test_dir = os.path.join(FILE_DIR, '_temps')
        create_test_dir(cls.test_dir)

        # Creating dummy default.ini file in utils.
        util_path = os.path.join(PACKAGE_PATH, 'utils', 'preferences')
        def_path = os.path.join(util_path, 'default.ini')

        # Making the preference manager look for info in test dir.
        default = ConfigObj(def_path)
        default['folder'] = cls.test_dir
        default['file'] = 'default_test.ini'
        default.write()

        # Creating a false template.
        template_path = os.path.join(cls.test_dir, 'temp_templates')
        os.mkdir(template_path)
        conf = ConfigObj()
        conf.filename = os.path.join(template_path, 'test.ini')
        conf.update(create_template_sequence())
        conf.write()

        # Saving plugin preferences.
        man_conf = {'templates_folders': repr([template_path])}

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
        util_path = os.path.join(PACKAGE_PATH, 'utils', 'preferences')
        def_path = os.path.join(util_path, 'default.ini')
        os.remove(def_path)

    def setup(self):

        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(DependenciesManifest())
        self.workbench.register(PulsesManagerManifest())

        self.plugin = self.workbench.get_plugin('hqc_meas.pulses')

    def teardown(self):
        self.workbench.unregister(u'hqc_meas.pulses')
        self.workbench.unregister(u'hqc_meas.dependencies')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_init(self):
        # Test the context is properly created at config init.
        seqs, _ = self.plugin.sequences_request(['Test'])
        _, conf, doc = seqs['Test']
        t_config = TemplateConfig(template_doc=doc, template_config=conf)

        assert_items_equal(t_config.context.logical_channels, ['A', 'B'])
        assert_items_equal(t_config.context.analogical_channels,
                           ['Ch1', 'Ch2'])
        assert_equal(t_config.context.channel_mapping,
                     {'A': '', 'B': '', 'Ch1': '', 'Ch2': ''})

    def test_building_template1(self):
        # Test building a template.
        seqs, _ = self.plugin.sequences_request(['Test'])
        _, conf, doc = seqs['Test']
        t_config = TemplateConfig(template_doc=doc, template_config=conf,
                                  manager=self.plugin)
        t_config.template_name = 'Test'

        seq = t_config.build_sequence()
        assert_false(t_config.errors)
        assert_is_instance(seq, TemplateSequence)
        assert_equal(seq.name, 'Test')
        # No need to check more as build_from_config is already tested in
        # test_template_sequence.

    def test_building_template2(self):
        # Test building a template for which some dependencies are missing.
        del self.plugin._sequences['Pulse']
        seqs, _ = self.plugin.sequences_request(['Test'])
        _, conf, doc = seqs['Test']
        t_config = TemplateConfig(template_doc=doc, template_config=conf,
                                  manager=self.plugin)
        t_config.template_name = 'Test'

        seq = t_config.build_sequence()
        assert_true(t_config.errors)
        assert_is(seq, None)

    def test_merging_template1(self):
        # Test merging a template.
        seqs, _ = self.plugin.sequences_request(['Test'])
        _, conf, doc = seqs['Test']
        test_conf = conf.copy()
        t_config = TemplateConfig(template_doc=doc, template_config=conf,
                                  manager=self.plugin)
        t_config.template_name = 'Test'
        t_config.merge = True
        t_config.root = RootSequence()
        t_config.context.channel_mapping =\
            {'A': 'Ch1_M1', 'Ch1': 'Ch3'}

        seq = t_config.build_sequence()
        assert_false(t_config.errors)
        assert_is_instance(seq, Sequence)
        assert_equal(seq.name, 'Test')
        loc_vars = literal_eval(test_conf['local_vars'])
        loc_vars.update(literal_eval(test_conf['template_vars']))
        assert_equal(seq.local_vars, loc_vars)
        assert_false(t_config.root.external_vars)

        assert_equal(seq.items[0].channel, 'Ch1_M1')
        assert_equal(seq.items[1].channel, '')
        assert_equal(seq.items[2].items[0].channel, '')
        assert_equal(seq.items[3].channel, 'Ch3')

    def test_merging_template2(self):
        # Test merging a template.
        seqs, _ = self.plugin.sequences_request(['Test'])
        _, conf, doc = seqs['Test']
        test_conf = conf.copy()
        t_config = TemplateConfig(template_doc=doc, template_config=conf,
                                  manager=self.plugin)
        t_config.template_name = 'Test'
        t_config.merge = True
        t_config.t_vars_as_root = True
        t_config.root = RootSequence()
        t_config.context.channel_mapping =\
            {'A': 'Ch1_M1', 'Ch1': 'Ch3'}

        seq = t_config.build_sequence()
        assert_false(t_config.errors)
        assert_is_instance(seq, Sequence)
        assert_equal(seq.name, 'Test')
        assert_equal(seq.local_vars, literal_eval(test_conf['local_vars']))
        assert_equal(t_config.root.external_vars,
                     literal_eval(test_conf['template_vars']))

        assert_equal(seq.items[0].channel, 'Ch1_M1')
        assert_equal(seq.items[1].channel, '')
        assert_equal(seq.items[2].items[0].channel, '')
        assert_equal(seq.items[3].channel, 'Ch3')
