# -*- coding: utf-8 -*-
import os
import shutil
from enaml.workbench.api import Workbench
import enaml
from configobj import ConfigObj

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.pref_manifest import PreferencesManifest
    from .pref_utils import PrefContributor


def setup_module():
    print __name__, ': setup_module() ~~~~~~~~~~~~~~~~~~~~~~'


def teardown_module():
    print __name__, ': teardown_module() ~~~~~~~~~~~~~~~~~~~'


class Test_State(object):

    test_dir = ''

    @classmethod
    def setup_class(cls):
        print __name__, ': ', cls.__name__, '.setup_class() ----------'
        # Creating dummy directory to store prefs during test
        directory = os.path.dirname(__file__)
        cls.test_dir = os.path.join(directory, '_tests')
        os.mkdir(cls.test_dir)

        # Creating dummy default.ini file in utils
        util_path = os.path.join(directory, '..', '..', 'hqc_meas', 'utils')
        def_path = os.path.join(util_path, 'default.ini')
        if os.path.isfile(def_path):
            os.rename(def_path, os.path.join(util_path, '__default.ini'))

        # Making the preference manager look for info in test dir
        default = ConfigObj(def_path)
        default['folder'] = cls.test_dir
        default['file'] = 'default_test.ini'
        default.write()

    @classmethod
    def teardown_class(cls):
        print __name__, ': ', cls.__name__, 'teardown_class() -------'
         # Removing test
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

    def teardown(self):
        path = os.path.join(self.test_dir, 'default_test.ini')
        if os.path.isfile(path):
            os.remove(path)

    def test_init(self):
        path = os.path.join(self.test_dir, 'default_test.ini')
        conf = ConfigObj(path)
        conf[u'test.prefs'] = {}
        conf[u'test.prefs']['string'] = 'test'
        conf.write()

        self.workbench.register(PreferencesManifest())
        self.workbench.register(PrefContributor())

        contrib = self.workbench.get_plugin(u'test.prefs')
        assert contrib.string == 'test'
        assert contrib.auto == ''

        pref_plugin = self.workbench.get_plugin(u'hqc_meas.preferences')
        pref_plugin.default_file = 'test.ini'

        self.workbench.unregister(u'test.prefs')
        self.workbench.unregister(u'hqc_meas.preferences')

        directory = os.path.dirname(__file__)
        util_path = os.path.join(directory, '..', '..', 'hqc_meas', 'utils')
        def_path = os.path.join(util_path, 'default.ini')
        def_conf = ConfigObj(def_path)
        assert def_conf['file'] == 'test.ini'
        def_conf['file'] = 'default_test.ini'
        def_conf.write()

    def test_get_plugin_pref1(self):
        self.workbench.register(PreferencesManifest())
        self.workbench.register(PrefContributor())

        core = self.workbench.get_plugin('enaml.workbench.core')
        pref = core.invoke_command('hqc_meas.preferences.get_plugin_prefs',
                                   {'plugin_id': u'test.prefs'}, self)
        assert pref == {}

    def test_get_plugin_pref2(self):
        path = os.path.join(self.test_dir, 'default_test.ini')
        conf = ConfigObj(path)
        conf[u'test.prefs'] = {}
        conf[u'test.prefs']['string'] = 'test'
        conf.write()

        self.workbench.register(PreferencesManifest())
        self.workbench.register(PrefContributor())

        core = self.workbench.get_plugin('enaml.workbench.core')
        pref = core.invoke_command('hqc_meas.preferences.get_plugin_prefs',
                                   {'plugin_id': u'test.prefs'}, self)
        assert pref['string'] == 'test'

    def test_update_prefs(self):
        self.workbench.register(PreferencesManifest())
        self.workbench.register(PrefContributor())

        contrib = self.workbench.get_plugin(u'test.prefs')
        contrib.string = 'test_update'
        core = self.workbench.get_plugin('enaml.workbench.core')
        core.invoke_command('hqc_meas.preferences.update_plugin_prefs',
                            {'plugin_id': u'test.prefs'}, self)

        pref_plugin = self.workbench.get_plugin(u'hqc_meas.preferences')
        assert pref_plugin._prefs == {u'test.prefs': {'string': 'test_update',
                                                      'auto': ''}}

    def test_auto_sync(self):
        self.workbench.register(PreferencesManifest())
        self.workbench.register(PrefContributor())

        contrib = self.workbench.get_plugin(u'test.prefs')
        contrib.auto = 'test_auto'

        ref = {u'test.prefs': {'auto': 'test_auto'}}
        pref_plugin = self.workbench.get_plugin(u'hqc_meas.preferences')
        assert pref_plugin._prefs == ref
        path = os.path.join(self.test_dir, 'default_test.ini')
        assert os.path.isfile(path)
        assert ConfigObj(path).dict() == ref

    def test_save1(self):
        self.workbench.register(PreferencesManifest())
        self.workbench.register(PrefContributor())

        contrib = self.workbench.get_plugin(u'test.prefs')
        contrib.string = 'test_save'
        core = self.workbench.get_plugin('enaml.workbench.core')
        core.invoke_command('hqc_meas.preferences.save', {}, self)

        path = os.path.join(self.test_dir, 'default_test.ini')
        ref = {u'test.prefs': {'string': 'test_save', 'auto': ''}}
        assert os.path.isfile(path)
        assert ConfigObj(path).dict() == ref

    def test_save2(self):
        self.workbench.register(PreferencesManifest())
        self.workbench.register(PrefContributor())

        contrib = self.workbench.get_plugin(u'test.prefs')
        contrib.string = 'test_save'

        path = os.path.join(self.test_dir, 'custom_test.ini')
        core = self.workbench.get_plugin('enaml.workbench.core')
        core.invoke_command('hqc_meas.preferences.save',
                            {'path': path}, self)

        ref = {u'test.prefs': {'string': 'test_save', 'auto': ''}}
        assert os.path.isfile(path)
        assert ConfigObj(path).dict() == ref

    def test_load1(self):
        self.workbench.register(PreferencesManifest())
        self.workbench.register(PrefContributor())

        path = os.path.join(self.test_dir, 'default_test.ini')
        conf = ConfigObj(path)
        conf[u'test.prefs'] = {}
        conf[u'test.prefs']['string'] = 'test'
        conf.write()

        core = self.workbench.get_plugin('enaml.workbench.core')
        core.invoke_command('hqc_meas.preferences.load',
                            {}, self)
        contrib = self.workbench.get_plugin(u'test.prefs')

        assert contrib.string == 'test'

    def test_load2(self):
        self.workbench.register(PreferencesManifest())
        self.workbench.register(PrefContributor())

        path = os.path.join(self.test_dir, 'default_test.ini')
        conf = ConfigObj(path)
        conf[u'test.prefs'] = {}
        conf[u'test.prefs']['string'] = 'test'
        conf.write()

        core = self.workbench.get_plugin('enaml.workbench.core')
        core.invoke_command('hqc_meas.preferences.load',
                            {'path': ''}, self)

    def test_load3(self):
        self.workbench.register(PreferencesManifest())
        self.workbench.register(PrefContributor())

        path = os.path.join(self.test_dir, 'custom_test.ini')
        conf = ConfigObj(path)
        conf[u'test.prefs'] = {}
        conf[u'test.prefs']['string'] = 'test'
        conf.write()

        core = self.workbench.get_plugin('enaml.workbench.core')
        core.invoke_command('hqc_meas.preferences.load',
                            {'path': path}, self)
        contrib = self.workbench.get_plugin(u'test.prefs')

        assert contrib.string == 'test'
