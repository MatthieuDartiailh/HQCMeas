# -*- coding: utf-8 -*-
import os
import shutil
from enaml.workbench.api import Workbench
import enaml
from configobj import ConfigObj

with enaml.imports():
    from hqc_meas.utils.core_manifest import HqcCoreManifest
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
        print __name__, ': TestClass.setup_class() ----------'
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
        print __name__, ': TestClass.teardown_class() -------'
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
        self.workbench.register(HqcCoreManifest())

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

        self.workbench.unregister(u'test.prefs')
        self.workbench.unregister(u'hqc_meas.preferences')
