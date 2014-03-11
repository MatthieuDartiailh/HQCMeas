# -*- coding: utf-8 -*-
#==============================================================================
# module : test_plugin.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
import enaml
import os
from configobj import ConfigObj
from nose.plugins.skip import SkipTest

from .tools import BaseClass

with enaml.imports():
    from hqc_meas.instruments.manager_manifest import InstrManagerManifest

    from .users import InstrUser1, InstrUser2, InstrUser3

from ..util import complete_line


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


class Test_TaskManagement(BaseClass):

    mod = __name__

    # TODO add test checking the failure recordings.
    def test_init(self):
        self.workbench.register(InstrManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.instr_manager')
        assert plugin.driver_types == ['Dummy']
        assert plugin.drivers == ['PanelTestDummy']
        assert plugin.all_profiles == ['Dummy']
        assert plugin.available_profiles == ['Dummy']

    def test_load_all(self):
        self.workbench.register(InstrManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.instr_manager')
        plugin.drivers_loading = []

        if plugin.report():
            raise SkipTest(plugin.report())

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
        from time import sleep
        sleep(0.1)
        assert plugin.all_profiles == sorted([u'Dummy', u'Test'])
        assert plugin.available_profiles == sorted([u'Dummy', u'Test'])
        os.remove(os.path.join(profile_path, 'test.ini'))
        sleep(0.1)
        assert plugin.all_profiles == sorted([u'Dummy'])
        assert plugin.available_profiles == sorted([u'Dummy'])

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

    def test_profile_request1(self):
        self.workbench.register(InstrManagerManifest())
        self.workbench.register(InstrUser1())
        user = self.workbench.get_plugin(u'test.user1')
        core = self.workbench.get_plugin(u'enaml.workbench.core')

        # Can get profile.
        core.invoke_command(u'hqc_meas.instr_manager.profiles_request',
                            {'profiles': [u'Dummy']}, user)
        manager = self.workbench.get_plugin(u'hqc_meas.instr_manager')
        assert manager.available_profiles == []
        assert manager._used_profiles == {'Dummy': u'test.user1'}

        # Can release profile.
        core.invoke_command(u'hqc_meas.instr_manager.profiles_released',
                            {'profiles': ['Dummy']}, user)
        assert manager.available_profiles == ['Dummy']
        assert manager._used_profiles == {}
        self.workbench.unregister(u'test.user1')

    def test_profiles_request2(self):
        self.workbench.register(InstrManagerManifest())
        self.workbench.register(InstrUser1())
        self.workbench.register(InstrUser2())
        user1 = self.workbench.get_plugin(u'test.user1')
        user2 = self.workbench.get_plugin(u'test.user2')
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        core.invoke_command(u'hqc_meas.instr_manager.profiles_request',
                            {'profiles': [u'Dummy']}, user1)

        # Can get profile if other user release it.
        core.invoke_command(u'hqc_meas.instr_manager.profiles_request',
                            {'profiles': [u'Dummy']}, user2)
        manager = self.workbench.get_plugin(u'hqc_meas.instr_manager')
        assert manager._used_profiles == {'Dummy': u'test.user2'}

        # Don't get profile if other user does not release, because method
        # fails
        core.invoke_command(u'hqc_meas.instr_manager.profiles_request',
                            {'profiles': [u'Dummy']}, user1)
        assert manager._used_profiles == {'Dummy': u'test.user2'}

        core.invoke_command(u'hqc_meas.instr_manager.profiles_released',
                            {'profiles': [u'Dummy']}, user2)
        self.workbench.unregister(u'test.user1')
        self.workbench.unregister(u'test.user2')

    def test_profiles_request3(self):
        self.workbench.register(InstrManagerManifest())
        self.workbench.register(InstrUser1())
        self.workbench.register(InstrUser3())
        user1 = self.workbench.get_plugin(u'test.user1')
        user3 = self.workbench.get_plugin(u'test.user3')
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        core.invoke_command(u'hqc_meas.instr_manager.profiles_request',
                            {'profiles': [u'Dummy']}, user1)

        # Can get profile if other user release it.
        core.invoke_command(u'hqc_meas.instr_manager.profiles_request',
                            {'profiles': [u'Dummy']}, user3)
        manager = self.workbench.get_plugin(u'hqc_meas.instr_manager')
        assert manager._used_profiles == {'Dummy': u'test.user3'}

        # Don't get profile if other user does not release because of its
        # policy
        core.invoke_command(u'hqc_meas.instr_manager.profiles_request',
                            {'profiles': [u'Dummy']}, user1)
        assert manager._used_profiles == {'Dummy': u'test.user3'}

        core.invoke_command(u'hqc_meas.instr_manager.profiles_released',
                            {'profiles': [u'Dummy']}, user3)
        self.workbench.unregister(u'test.user1')
        self.workbench.unregister(u'test.user3')
