# -*- coding: utf-8 -*-
from enaml.workbench.api import Workbench
import enaml
import os
import shutil
from configobj import ConfigObj
from nose.tools import assert_in, assert_not_in, assert_equal, raises

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from hqc_meas.utils.pref_manifest import PreferencesManifest
    from hqc_meas.measurement.manifest import MeasureManifest

    from .dummies import (DummyCheck1, DummyCheck1bis, DummyCheck2,
                          DummyCheck3, DummyCheck4,
                          DummyHeader1, DummyHeader1bis, DummyHeader2,
                          DummyHeader3, DummyHeader4,
                          DummyEditor1, DummyEditor1bis, DummyEditor2,
                          DummyEditor3, DummyEditor4,
                          DummyMonitor1, DummyMonitor1bis, DummyMonitor2,
                          DummyMonitor3, DummyMonitor4,
                          DummyEngine1, DummyEngine1bis, DummyEngine2,
                          DummyEngine3, DummyEngine4)

from ..util import complete_line


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


class TestPluginCoreFunctionalities(object):

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

        conf = ConfigObj(os.path.join(cls.test_dir, 'default_test.ini'))
        conf[u'hqc_meas.measure'] = {}
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
        self.workbench.unregister(u'hqc_meas.measure')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_init(self):
        """ Test automatic registration at init.

        """
        # Tamper with prefs to alter startup.
        pref_plugin = self.workbench.get_plugin(u'hqc_meas.preferences')
        prefs = {'manifests': repr([('tests.measurement.dummies',
                                    'DummyCheck1')])}
        pref_plugin._prefs[u'hqc_meas.measure'].update(prefs)

        self.workbench.register(MeasureManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        pref_plugin._prefs[u'hqc_meas.measure'] = {}

        assert_in(u'dummy.check1', plugin._manifest_ids)
        assert_in(u'dummy.check1', plugin.checks)

        # Automatically registered plugins are automatically unregistered.

    #--- Checks tests ---------------------------------------------------------

    def test_check_registation1(self):
        """ Test that checks are properly found at start-up.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyCheck1())
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')

        assert_in(u'dummy.check1', plugin.checks)

        self.workbench.unregister(u'dummy.check1')

        assert_not_in(u'dummy.check1', plugin.checks)

    def test_check_registration2(self):
        """ Test checks update when a new plugin is registered.

        """
        self.workbench.register(MeasureManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        self.workbench.register(DummyCheck1())

        assert_in(u'dummy.check1', plugin.checks)

        self.workbench.unregister(u'dummy.check1')

        assert_not_in(u'dummy.check1', plugin.checks)

    def test_check_factory(self):
        """ Test getting the Check decl from a factory.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyCheck3())
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')

        assert_in(u'dummy.check3', plugin.checks)

        self.workbench.unregister(u'dummy.check3')

        assert_not_in(u'dummy.check3', plugin.checks)

    @raises(ValueError)
    def test_check_errors1(self):
        """ Test uniqueness of check id.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyCheck1())
        self.workbench.register(DummyCheck1bis())
        self.workbench.get_plugin(u'hqc_meas.measure')

    @raises(ValueError)
    def test_check_errors2(self):
        """ Test presence of perfom_test in Check.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyCheck2())
        self.workbench.get_plugin(u'hqc_meas.measure')

    @raises(TypeError)
    def test_check_errors3(self):
        """ Test enforcement of type for Check when using factory.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyCheck4())
        self.workbench.get_plugin(u'hqc_meas.measure')

    #--- Headers tests --------------------------------------------------------

    def test_header_registation1(self):
        """ Test that headers are properly found at start-up.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyHeader1())
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')

        assert_in(u'dummy.header1', plugin.headers)

        self.workbench.unregister(u'dummy.header1')

        assert_not_in(u'dummy.header1', plugin.headers)

    def test_header_registration2(self):
        """ Test headers update when a new plugin is registered.

        """
        self.workbench.register(MeasureManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        self.workbench.register(DummyHeader1())

        assert_in(u'dummy.header1', plugin.headers)

        self.workbench.unregister(u'dummy.header1')

        assert_not_in(u'dummy.header1', plugin.headers)

    def test_header_factory(self):
        """ Test getting the Header decl from a factory.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyHeader3())
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')

        assert_in(u'dummy.header3', plugin.headers)

        self.workbench.unregister(u'dummy.header3')

        assert_not_in(u'dummy.header3', plugin.headers)

    @raises(ValueError)
    def test_header_errors1(self):
        """ Test uniqueness of header id.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyHeader1())
        self.workbench.register(DummyHeader1bis())
        self.workbench.get_plugin(u'hqc_meas.measure')

    @raises(ValueError)
    def test_header_errors2(self):
        """ Test presence of build_header in Header.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyHeader2())
        self.workbench.get_plugin(u'hqc_meas.measure')

    @raises(TypeError)
    def test_header_errors3(self):
        """ Test enforcement of type for Header when using factory.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyHeader4())
        self.workbench.get_plugin(u'hqc_meas.measure')

    #--- Editors tests --------------------------------------------------------

    def test_editor_registation1(self):
        """ Test that editors are properly found at start-up.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyEditor1())
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')

        assert_in(u'dummy.editor1', plugin.editors)

        self.workbench.unregister(u'dummy.editor1')

        assert_not_in(u'dummy.editor1', plugin.editors)

    def test_editor_registration2(self):
        """ Test editors update when a new plugin is registered.

        """
        self.workbench.register(MeasureManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        self.workbench.register(DummyEditor1())

        assert_in(u'dummy.editor1', plugin.editors)

        self.workbench.unregister(u'dummy.editor1')

        assert_not_in(u'dummy.editor1', plugin.editors)

    def test_editor_factory(self):
        """ Test getting the Editor decl from a factory.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyEditor3())
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')

        assert_in(u'dummy.editor3', plugin.editors)

        self.workbench.unregister(u'dummy.editor3')

        assert_not_in(u'dummy.editor3', plugin.editors)

    @raises(ValueError)
    def test_editor_errors1(self):
        """ Test uniqueness of editor id.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyEditor1())
        self.workbench.register(DummyEditor1bis())
        self.workbench.get_plugin(u'hqc_meas.measure')

    @raises(ValueError)
    def test_editor_errors2(self):
        """ Test presence of factory in Editor.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyEditor2())
        self.workbench.get_plugin(u'hqc_meas.measure')

    @raises(TypeError)
    def test_editor_errors3(self):
        """ Test enforcement of type for Editor when using factory.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyEditor4())
        self.workbench.get_plugin(u'hqc_meas.measure')

    #--- Monitors tests -------------------------------------------------------

    def test_monitor_registation1(self):
        """ Test that monitors are properly found at start-up.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyMonitor1())
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')

        assert_in(u'dummy.monitor1', plugin.monitors)

        self.workbench.unregister(u'dummy.monitor1')

        assert_not_in(u'dummy.monitor1', plugin.monitors)

    def test_monitor_registration2(self):
        """ Test monitors update when a new plugin is registered.

        """
        self.workbench.register(MeasureManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        self.workbench.register(DummyMonitor1())

        assert_in(u'dummy.monitor1', plugin.monitors)

        self.workbench.unregister(u'dummy.monitor1')

        assert_not_in(u'dummy.monitor1', plugin.monitors)

    def test_monitor_factory(self):
        """ Test getting the Monitor decl from a factory.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyMonitor3())
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')

        assert_in(u'dummy.monitor3', plugin.monitors)

        self.workbench.unregister(u'dummy.monitor3')

        assert_not_in(u'dummy.monitor3', plugin.monitors)

    @raises(ValueError)
    def test_monitor_errors1(self):
        """ Test uniqueness of monitor id.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyMonitor1())
        self.workbench.register(DummyMonitor1bis())
        self.workbench.get_plugin(u'hqc_meas.measure')

    @raises(ValueError)
    def test_monitor_errors2(self):
        """ Test presence of factory in Monitor.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyMonitor2())
        self.workbench.get_plugin(u'hqc_meas.measure')

    @raises(TypeError)
    def test_monitor_errors3(self):
        """ Test enforcement of type for Monitor when using factory.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyMonitor4())
        self.workbench.get_plugin(u'hqc_meas.measure')

    #--- Engines tests --------------------------------------------------------

    def test_engine_registation1(self):
        """ Test that engines are properly found at start-up.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyEngine1())
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')

        assert_in(u'dummy.engine1', plugin.engines)

        self.workbench.unregister(u'dummy.engine1')

        assert_not_in(u'dummy.engine1', plugin.engines)

    def test_engine_registration2(self):
        """ Test engines update when a new plugin is registered.

        """
        self.workbench.register(MeasureManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        self.workbench.register(DummyEngine1())

        assert_in(u'dummy.engine1', plugin.engines)

        self.workbench.unregister(u'dummy.engine1')

        assert_not_in(u'dummy.engine1', plugin.engines)

    def test_engine_factory(self):
        """ Test getting the Engine decl from a factory.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyEngine3())
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')

        assert_in(u'dummy.engine3', plugin.engines)

        self.workbench.unregister(u'dummy.engine3')

        assert_not_in(u'dummy.engine3', plugin.engines)

    @raises(ValueError)
    def test_engine_errors1(self):
        """ Test uniqueness of engine id.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyEngine1())
        self.workbench.register(DummyEngine1bis())
        self.workbench.get_plugin(u'hqc_meas.measure')

    @raises(ValueError)
    def test_engine_errors2(self):
        """ Test presence of factory in Engine.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyEngine2())
        self.workbench.get_plugin(u'hqc_meas.measure')

    @raises(TypeError)
    def test_engine_errors3(self):
        """ Test enforcement of type for Engine when using factory.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyEngine4())
        self.workbench.get_plugin(u'hqc_meas.measure')

    def test_selected_engine1(self):
        """ Test selected engine from preferences is kept if found.

        """
        # Tamper with prefs to alter startup.
        pref_plugin = self.workbench.get_plugin(u'hqc_meas.preferences')
        prefs = {'selected_engine': u'dummy.engine1'}
        pref_plugin._prefs[u'hqc_meas.measure'].update(prefs)

        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyEngine1())
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        pref_plugin._prefs[u'hqc_meas.measure'] = {}

        assert_equal(plugin.selected_engine, u'dummy.engine1')
        assert plugin.engines[u'dummy.engine1'].post_selected

        self.workbench.unregister(u'dummy.engine1')

    def test_selected_engine2(self):
        """ Test selected engine from preferences is deleted if not found.

        """
        # Tamper with prefs to alter startup.
        pref_plugin = self.workbench.get_plugin(u'hqc_meas.preferences')
        prefs = {'selected_engine': u'dummy.engine1'}
        pref_plugin._prefs[u'hqc_meas.measure'].update(prefs)

        self.workbench.register(MeasureManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        pref_plugin._prefs[u'hqc_meas.measure'] = {}

        assert_equal(plugin.selected_engine, u'')

    def test_selected_engine3(self):
        """ Test observer is called when new engine selected.

        """
        self.workbench.register(MeasureManifest())
        self.workbench.register(DummyEngine1())
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')

        plugin.selected_engine = u'dummy.engine1'

        assert plugin.engines[u'dummy.engine1'].post_selected

        plugin.selected_engine = u''

        assert plugin.engines[u'dummy.engine1'].post_deselected
