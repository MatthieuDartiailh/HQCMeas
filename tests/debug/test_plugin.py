# -*- coding: utf-8 -*-
from enaml.workbench.api import Workbench
import enaml
import os
import shutil
from configobj import ConfigObj
from nose.tools import assert_in, assert_not_in, raises, assert_false

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from hqc_meas.utils.pref_manifest import PreferencesManifest
    from hqc_meas.debug.debugger_manifest import DebuggerManifest

    from .dummies import (DummyDebugger1, DummyDebugger1bis,
                          DummyDebugger2, DummyDebugger2bis,
                          DummyDebugger3, DummyDebugger4)


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
        conf[u'hqc_meas.debug'] = {}
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
        self.workbench.unregister(u'hqc_meas.debug')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_init(self):
        """ Test automatic registration at init.

        """
        # Tamper with prefs to alter startup.
        pref_plugin = self.workbench.get_plugin(u'hqc_meas.preferences')
        prefs = {'manifests': repr([('tests.debug.dummies',
                                    'DummyDebugger1')])}
        pref_plugin._prefs[u'hqc_meas.debug'].update(prefs)

        self.workbench.register(DebuggerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.debug')
        pref_plugin._prefs[u'hqc_meas.debug'] = {}

        assert_in(u'dummy.debugger1', plugin._manifest_ids)
        assert_in(u'dummy.debugger1', plugin.debuggers)

        # Automatically registered plugins are automatically unregistered.

    #--- Debuggers tests ------------------------------------------------------

    def test_check_registation1(self):
        """ Test that debuggers are properly found at start-up.

        """
        self.workbench.register(DebuggerManifest())
        self.workbench.register(DummyDebugger1())
        plugin = self.workbench.get_plugin(u'hqc_meas.debug')

        assert_in(u'dummy.debugger1', plugin.debuggers)

        self.workbench.unregister(u'dummy.debugger1')

        assert_not_in(u'dummy.debugger1', plugin.debuggers)
        assert_false(plugin._debugger_extensions)

    def test_check_registration2(self):
        """ Test debuggers update when a new plugin is registered.

        """
        self.workbench.register(DebuggerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.debug')
        self.workbench.register(DummyDebugger1())

        assert_in(u'dummy.debugger1', plugin.debuggers)

        self.workbench.unregister(u'dummy.debugger1')

        assert_not_in(u'dummy.debugger1', plugin.debuggers)

    def test_check_factory(self):
        """ Test getting the Debugger decl from a factory.

        """
        self.workbench.register(DebuggerManifest())
        self.workbench.register(DummyDebugger3())
        plugin = self.workbench.get_plugin(u'hqc_meas.debug')

        assert_in(u'dummy.debugger3', plugin.debuggers)

        self.workbench.unregister(u'dummy.debugger3')

        assert_not_in(u'dummy.debugger3', plugin.debuggers)

    @raises(ValueError)
    def test_check_errors1(self):
        """ Test uniqueness of Debugger id.

        """
        self.workbench.register(DebuggerManifest())
        self.workbench.register(DummyDebugger1())
        self.workbench.register(DummyDebugger1bis())
        self.workbench.get_plugin(u'hqc_meas.debug')

    @raises(ValueError)
    def test_check_errors2(self):
        """ Test presence of factory in Debugger.

        """
        self.workbench.register(DebuggerManifest())
        self.workbench.register(DummyDebugger2())
        self.workbench.get_plugin(u'hqc_meas.debug')

    @raises(ValueError)
    def test_check_errors2bis(self):
        """ Test presence of view in Debugger.

        """
        self.workbench.register(DebuggerManifest())
        self.workbench.register(DummyDebugger2bis())
        self.workbench.get_plugin(u'hqc_meas.debug')

    @raises(TypeError)
    def test_check_errors3(self):
        """ Test enforcement of type for Debugger when using factory.

        """
        self.workbench.register(DebuggerManifest())
        self.workbench.register(DummyDebugger4())
        self.workbench.get_plugin(u'hqc_meas.debug')
