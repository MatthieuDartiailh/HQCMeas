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
from nose.tools import assert_equal, assert_in, assert_not_in
from nose.plugins.skip import SkipTest

from .tools import BaseClass

with enaml.imports():
    from hqc_meas.instruments.manager_manifest import InstrManagerManifest
    from hqc_meas.instruments.forms import FORMS, FORMS_MAP_VIEWS

    from .users import InstrUser1, InstrUser2, InstrUser3

from ..util import complete_line, process_app_events


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


class Test_DriverManagement(BaseClass):

    mod = __name__

    def test_init(self):
        self.workbench.register(InstrManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.instr_manager')
        assert_equal(plugin.driver_types, ['Dummy'])
        assert_in('PanelTestDummy', plugin.drivers)
        assert_in('Dummy', plugin.all_profiles)
        assert_in('Dummy', plugin.available_profiles)

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
        assert_equal(plugin._users.keys(), [u'test.user1'])
        self.workbench.register(InstrUser2())
        assert_equal(sorted(plugin._users.keys()),
                     sorted([u'test.user1', u'test.user2']))
        self.workbench.unregister(u'test.user2')
        assert_equal(plugin._users.keys(), [u'test.user1'])

    def test_profile_observation(self):
        self.workbench.register(InstrManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.instr_manager')
        assert_in('Dummy', plugin.all_profiles)
        assert_in('Dummy', plugin.available_profiles)
        profile_path = os.path.join(self.test_dir, 'temp_profiles')
        prof = ConfigObj(os.path.join(profile_path, 'test.ini'))
        prof['driver_type'] = 'Dummy'
        prof['driver'] = 'PanelTestDummy'
        prof.write()
        from time import sleep
        sleep(0.1)
        process_app_events()
        assert_in(u'Test', plugin.all_profiles)
        assert_in(u'Test', plugin.available_profiles)
        os.remove(os.path.join(profile_path, 'test.ini'))
        sleep(0.1)
        process_app_events()
        assert_not_in(u'Test', plugin.all_profiles)
        assert_not_in(u'Test', plugin.available_profiles)

    def test_driver_types_request1(self):
        self.workbench.register(InstrManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.instr_manager.driver_types_request'
        d_types, missing = core.invoke_command(com,
                                               {'driver_types': ['Dummy']},
                                               self)

        assert_equal(d_types.keys(), ['Dummy'])
        assert_equal(d_types['Dummy'].__name__, 'DummyInstrument')
        assert_equal(missing, [])

    def test_driver_types_request2(self):
        self.workbench.register(InstrManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        invoke = core.invoke_command

        com = u'hqc_meas.instr_manager.driver_types_request'
        d_types, missing = invoke(com, {'driver_types': ['Dummy', 'N']}, self)

        assert_equal(missing, ['N'])
        assert_equal(d_types.keys(), ['Dummy'])

    def test_drivers_request1(self):
        self.workbench.register(InstrManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.instr_manager.drivers_request'
        drivers, missing = core.invoke_command(com,
                                               {'drivers': ['PanelTestDummy']},
                                               self)

        assert_equal(drivers.keys(), ['PanelTestDummy'])
        assert_equal(drivers['PanelTestDummy'].__name__, 'PanelTestDummy')
        assert_equal(missing, [])

    def test_drivers_request2(self):
        self.workbench.register(InstrManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        invoke = core.invoke_command

        com = u'hqc_meas.instr_manager.drivers_request'
        drivers, missing = invoke(com,
                                  {'drivers': ['PanelTestDummy', 'N']},
                                  self)

        assert_equal(drivers.keys(), ['PanelTestDummy'])
        assert_equal(drivers['PanelTestDummy'].__name__, 'PanelTestDummy')
        assert_equal(missing, ['N'])

    def test_matching_drivers(self):
        self.workbench.register(InstrManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.instr_manager.matching_drivers'
        driver_names = core.invoke_command(com, {'driver_types': ['Dummy']},
                                           self)
        assert_in('PanelTestDummy', driver_names)

    def test_matching_form1(self):
        self.workbench.register(InstrManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.instr_manager.matching_form'
        form = core.invoke_command(com, {'driver': 'Dummy'}, self)
        assert_equal(form, FORMS['Dummy'])

    def test_matching_form2(self):
        self.workbench.register(InstrManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.instr_manager.matching_form'
        form = core.invoke_command(com, {'driver': 'PanelTestDummy'}, self)
        assert_equal(form, FORMS['Dummy'])

    def test_matching_form3(self):
        self.workbench.register(InstrManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.instr_manager.matching_form'
        form, view = core.invoke_command(com, {'driver': '__xxxx__',
                                               'view': True}, self)
        assert_equal(form, None)
        assert_equal(view, FORMS_MAP_VIEWS[type(None)])

    def test_matching_profiles(self):
        self.workbench.register(InstrManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.instr_manager.matching_profiles'
        [prof_name] = core.invoke_command(com,
                                          {'drivers': ['PanelTestDummy']},
                                          self)
        assert_equal(prof_name, 'Dummy')

    def test_profile_path1(self):
        self.workbench.register(InstrManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.instr_manager')
        path = plugin.profile_path('Dummy')
        assert_equal(path, os.path.join(self.test_dir,
                                        'temp_profiles',
                                        'dummy.ini'))

    def test_profile_path2(self):
        self.workbench.register(InstrManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.instr_manager')
        path = plugin.profile_path('N')
        assert path is None

    def test_profile_request1(self):
        self.workbench.register(InstrManagerManifest())
        self.workbench.register(InstrUser1())
        user = self.workbench.get_plugin(u'test.user1')
        core = self.workbench.get_plugin(u'enaml.workbench.core')

        # Can get profile.
        cmd = u'hqc_meas.instr_manager.profiles_request'
        profs, miss = core.invoke_command(cmd, {'profiles': [u'Dummy']}, user)
        manager = self.workbench.get_plugin(u'hqc_meas.instr_manager')

        assert_equal(manager.available_profiles, [])
        assert_equal(manager._used_profiles, {'Dummy': u'test.user1'})

        # Can release profile.
        core.invoke_command(u'hqc_meas.instr_manager.profiles_released',
                            {'profiles': ['Dummy']}, user)

        assert_equal(manager.available_profiles, ['Dummy'])
        assert_equal(manager._used_profiles, {})

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

        assert_equal(manager._used_profiles, {'Dummy': u'test.user2'})

        # Don't get profile if other user does not release, because method
        # fails
        core.invoke_command(u'hqc_meas.instr_manager.profiles_request',
                            {'profiles': [u'Dummy']}, user1)

        assert_equal(manager._used_profiles, {'Dummy': u'test.user2'})

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

        assert_equal(manager._used_profiles, {'Dummy': u'test.user3'})

        # Don't get profile if other user does not release because of its
        # policy
        core.invoke_command(u'hqc_meas.instr_manager.profiles_request',
                            {'profiles': [u'Dummy']}, user1)

        assert_equal(manager._used_profiles, {'Dummy': u'test.user3'})

        core.invoke_command(u'hqc_meas.instr_manager.profiles_released',
                            {'profiles': [u'Dummy']}, user3)
        self.workbench.unregister(u'test.user1')
        self.workbench.unregister(u'test.user3')

    def test_profile_request4(self):
        self.workbench.register(InstrManagerManifest())
        self.workbench.register(InstrUser1())
        user = self.workbench.get_plugin(u'test.user1')
        core = self.workbench.get_plugin(u'enaml.workbench.core')

        # Can get profile.
        cmd = u'hqc_meas.instr_manager.profiles_request'
        _, miss = core.invoke_command(cmd,
                                      {'profiles': [u'N']},
                                      user)
        manager = self.workbench.get_plugin(u'hqc_meas.instr_manager')

        assert_equal(manager.available_profiles, ['Dummy'])
        assert_equal(manager._used_profiles, {})
        assert_equal(miss, [u'N'])

        self.workbench.unregister(u'test.user1')
