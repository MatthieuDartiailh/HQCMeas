# -*- coding: utf-8 -*-
from enaml.workbench.api import Workbench
import enaml
import os
import shutil
from configobj import ConfigObj

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from hqc_meas.utils.pref_manifest import PreferencesManifest
    from hqc_meas.instruments.manager_manifest import InstrManagerManifest

    from .users import InstrUser1, InstrUser2, InstrUser3


def setup_module():
    print __name__, ': setup_module() ~~~~~~~~~~~~~~~~~~~~~~'


def teardown_module():
    print __name__, ': teardown_module() ~~~~~~~~~~~~~~~~~~~'


class Test_TaskManagement(object):

    test_dir = ''

    @classmethod
    def setup_class(cls):
        print __name__, ': TestClass.setup_class() ----------'
        # Creating dummy directory for prefs (avoid prefs interferences).
        directory = os.path.dirname(__file__)
        cls.test_dir = os.path.join(directory, '_tests')
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

        # Creating driver preferences.
        driv_path = os.path.join(directory, '..', '..', 'hqc_meas',
                                 'instruments', 'drivers')
        driv_api = set(('driver_tools.py', 'dummy.py'))
        driv_loading = [('drivers.' + mod[:-3])
                        for mod in os.listdir(driv_path)
                        if mod.endswith('.py') and mod not in driv_api]

        # Creating false profile.
        profile_path = os.path.join(cls.test_dir, 'temp_profiles')
        os.mkdir(profile_path)
        prof = ConfigObj(os.path.join(profile_path, 'dummy.ini'))
        prof['driver_type'] = 'Dummy'
        prof['driver_class'] = 'PanelTestDummy'
        prof.write()

        # Saving plugin preferences.
        man_conf = {'drivers_loading': str(driv_loading),
                    'profiles_folders': str([profile_path])}

        conf = ConfigObj(os.path.join(cls.test_dir, 'default_test.ini'))
        conf['hqc_meas.instr_manager'] = {}
        conf['hqc_meas.instr_manager'].update(man_conf)
        conf.write()

    @classmethod
    def teardown_class(cls):
        print __name__, ': TestClass.teardown_class() -------'
         # Removing .ini files created during tests.
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
        pass

    def test_init(self):
        self.workbench.register(InstrManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.instr_manager')
        assert plugin.driver_types == ['Dummy']
        assert plugin.drivers == ['PanelTestDummy']
        assert plugin.all_profiles == ['Dummy']
        assert plugin.available_profiles == ['Dummy']

    def test_user_management(self):
        self.workbench.register(InstrManagerManifest())
        self.workbench.register(InstrUser1())
        plugin = self.workbench.get_plugin(u'hqc_meas.instr_manager')
        assert plugin._users.keys() == [u'test.user1']
        self.workbench.register(InstrUser2())
        assert sorted(plugin._users.keys()) ==\
            sorted([u'test.user1', u'test.user2'])
        self.workbench.unregister(u'test.user2')
        assert plugin._users.keys() == [u'test.user1']

    def test_profile_observation(self):
        self.workbench.register(InstrManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.instr_manager')
        assert plugin.all_profiles == ['Dummy']
        assert plugin.available_profiles == ['Dummy']
        profile_path = os.path.join(self.test_dir, 'temp_profiles')
        prof = ConfigObj(os.path.join(profile_path, 'test.ini'))
        prof['driver_type'] = 'Dummy'
        prof['driver_class'] = 'PanelTestDummy'
        prof.write()
        assert plugin.all_profiles == ['Dummy', 'Test']
        assert plugin.available_profiles == ['Dummy', 'Test']

    def test_driver_types_request(self):
        self.workbench.register(InstrManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.instr_manager.driver_types_request'
        d_types = core.invoke_command(com, {'driver_types': ['Dummy']}, self)
        from hqc_meas.instruments.drivers.dummy import DummyInstrument
        assert d_types.keys() == ['Dummy']
        assert d_types.values() == [DummyInstrument]

    def test_drivers_request(self):
        self.workbench.register(InstrManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.instr_manager.drivers_request'
        drivers = core.invoke_command(com, {'drivers': ['PanelTestDummy']},
                                      self)
        from hqc_meas.instruments.drivers.dummies.panel_dummy\
            import PanelTestDummy
        assert drivers.keys() == ['PanelTestDummy']
        assert drivers.values() == [PanelTestDummy]

    def test_matching_drivers(self):
        self.workbench.register(InstrManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.instr_manager.matching_drivers'
        [driver_name] = core.invoke_command(com, {'driver_types': ['Dummy']},
                                            self)
        assert driver_name == 'PanelTestDummy'

    def test_matching_profiles(self):
        self.workbench.register(InstrManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.instr_manager.matching_profiles'
        [prof_name] = core.invoke_command(com, {'drivers': ['PanelTestDummy']},
                                          self)
        assert prof_name == 'Dummy'

    def test_profile_path(self):
        self.workbench.register(InstrManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.instr_manager')
        path = plugin.profile_path('Dummy')
        assert path == os.path.join(self.test_dir,
                                    'temp_profiles',
                                    'dummy.ini')
