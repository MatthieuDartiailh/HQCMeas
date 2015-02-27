# -*- coding: utf-8 -*-
# =============================================================================
# module : test_set_dc_voltage.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from nose.tools import (assert_equal, assert_true, assert_false, assert_in,
                        assert_is_instance, assert_is)
from nose.plugins.attrib import attr
from multiprocessing import Event
from enaml.workbench.api import Workbench

from hqc_meas.tasks.api import RootTask
from hqc_meas.tasks.tasks_instr.set_dc_voltage_task\
    import (SetDCVoltageTask,
            MultiChannelVoltageSourceInterface)

import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state.manifest import StateManifest
    from hqc_meas.utils.preferences.manifest import PreferencesManifest
    from hqc_meas.tasks.manager.manifest import TaskManagerManifest
    from hqc_meas.instruments.manager.manifest import InstrManagerManifest

    from hqc_meas.tasks.tasks_instr.views.set_dc_voltage_view\
        import SetDcVoltageView

from ...util import process_app_events, close_all_windows
from .instr_helper import InstrHelper


class TestSetDCVoltageTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SetDCVoltageTask(task_name='Test')
        self.root.children_task.append(self.task)
        self.root.run_time['drivers'] = {'Test': InstrHelper}

        self.task.back_step = 0.1
        self.task.delay = 0.1

        # This is set simply to make sure the test of InstrTask pass.
        self.task.selected_driver = 'Test'
        self.task.selected_profile = 'Test1'

    def test_check_base_interface1(self):
        # Simply test that everything is ok if voltage can be evaluated.
        self.task.target_value = '1.0'

        test, traceback = self.task.check(test_instr=True)
        assert_true(test)
        assert_false(traceback)

    def test_check_base_interface2(self):
        # Check handling a wrong voltage.
        self.task.target_value = '*1.0*'

        test, traceback = self.task.check(test_instr=True)
        assert_false(test)
        assert_equal(len(traceback), 1)

    def test_check_multichannel_interface1(self):
        # Check the multichannel specific tests, passing.
        interface = MultiChannelVoltageSourceInterface(task=self.task)
        interface.channel = 1
        self.task.interface = interface
        self.task.target_value = '1.0'

        profile = {'Test1': ({'defined_channels': [[1]]},
                             {})}
        self.root.run_time['profiles'] = profile

        test, traceback = self.task.check(test_instr=True)
        assert_true(test)
        assert_false(traceback)

    def test_check_multichannel_interface2(self):
        # Check the multichannel specific tests, failing = driver.
        interface = MultiChannelVoltageSourceInterface(task=self.task)
        interface.channel = 1
        self.task.interface = interface
        self.task.target_value = '1.0'

        self.root.run_time['drivers'] = {}
        profile = {'Test1': ({'defined_channels': [[1]]},
                             {})}
        self.root.run_time['profiles'] = profile

        test, traceback = self.task.check(test_instr=True)
        assert_false(test)
        assert_equal(len(traceback), 1)

    def test_check_multichannel_interface3(self):
        # Check the multichannel specific tests, failing =profile.
        interface = MultiChannelVoltageSourceInterface(task=self.task)
        interface.channel = 1
        self.task.interface = interface
        self.task.target_value = '1.0'
        self.task.selected_profile = ''

        self.root.run_time['drivers'] = {'Test': InstrHelper}

        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)

    def test_check_multichannel_interface4(self):
        # Check the multichannel specific tests, failing = channel.
        interface = MultiChannelVoltageSourceInterface(task=self.task)
        interface.channel = 2
        self.task.interface = interface
        self.task.target_value = '1.0'

        profile = {'Test1': ({'defined_channels': [[1]]},
                             {})}
        self.root.run_time['profiles'] = profile
        self.root.run_time['drivers'] = {'Test': InstrHelper}

        test, traceback = self.task.check(test_instr=True)
        assert_false(test)
        assert_equal(len(traceback), 1)

    def test_smooth_set_stopping(self):
        self.root.run_time['profiles'] = {'Test1': ({'voltage': [0.0],
                                                     'funtion': ['VOLT'],
                                                     'owner': [None]}, {})}

        self.root.task_database.prepare_for_running()
        self.root.should_stop.set()

        setter = lambda value: setattr(self.driver, 'voltage', value)

        self.task.smooth_set(1.0, setter, 0.0)
        assert_equal(self.root.get_from_database('Test_voltage'), 0.0)

    def test_perform_base_interface(self):
        # Test also that a target which is not a multiple of the back step
        # is correctly handled.
        self.task.target_value = '0.05'

        self.root.run_time['profiles'] = {'Test1': ({'voltage': [0.0],
                                                     'funtion': ['VOLT'],
                                                     'owner': [None]}, {})}

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_voltage'), 0.05)
        self.task.target_value = '1.06'
        self.task.perform()
        assert_equal(self.root.get_from_database('Test_voltage'), 1.06)

    def test_perform_multichannel_interface(self):
        interface = MultiChannelVoltageSourceInterface(task=self.task)
        interface.channel = 1
        self.task.interface = interface
        self.task.target_value = '1.0'

        profile = {'Test1': ({'voltage': [0.0],
                              'funtion': ['VOLT'],
                              'owner': [None]},
                             {'get_channel': lambda x, i: x}
                             )}
        self.root.run_time['profiles'] = profile

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_voltage'), 1.0)


@attr('ui')
class TestSetDCVoltageView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(InstrManagerManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SetDCVoltageTask(task_name='Test')
        self.root.children_task.append(self.task)
        self.root.run_time['drivers'] = {'Test': InstrHelper}

        self.task.back_step = 0.1
        self.task.delay = 0.1

    def teardown(self):
        close_all_windows()

        self.workbench.unregister(u'hqc_meas.task_manager')
        self.workbench.unregister(u'hqc_meas.instr_manager')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_view1(self):
        # Intantiate a view with no selected interface and select one after
        window = enaml.widgets.api.Window()
        core = self.workbench.get_plugin('enaml.workbench.core')
        view = SetDcVoltageView(window, task=self.task, core=core)
        window.show()

        process_app_events()

        assert_in('YokogawaGS200', view.drivers)
        self.task.selected_driver = 'YokogawaGS200'
        process_app_events()
        assert_is(self.task.interface, None)

        assert_in('TinyBilt', view.drivers)
        self.task.selected_driver = 'TinyBilt'
        process_app_events()
        assert_is_instance(self.task.interface,
                           MultiChannelVoltageSourceInterface)

    def test_view2(self):
        # Intantiate a view with a selected interface.
        interface = MultiChannelVoltageSourceInterface(task=self.task)
        self.task.interface = interface
        self.task.target_value = '1.0'
        self.task.selected_driver = 'TinyBilt'

        interface = self.task.interface

        window = enaml.widgets.api.Window()
        core = self.workbench.get_plugin('enaml.workbench.core')
        SetDcVoltageView(window, task=self.task, core=core)
        window.show()

        process_app_events()

        assert_is(self.task.interface, interface)
