# -*- coding: utf-8 -*-
#==============================================================================
# module : test_set_dc_voltage.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from nose.tools import (assert_equal, assert_true, assert_false, assert_in,
                        assert_is_instance, assert_is, assert_not_in)
from nose.plugins.attrib import attr
from multiprocessing import Event
from enaml.workbench.api import Workbench

from hqc_meas.tasks.api import RootTask
from hqc_meas.tasks.tasks_util.test_tasks import PrintTask
from hqc_meas.tasks.tasks_logic.loop_task import LoopTask
from hqc_meas.tasks.tasks_logic.loop_iterable_interface\
     import IterableLoopInterface
from hqc_meas.tasks.tasks_logic.loop_linspace_interface\
     import LinspaceLoopInterface

import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from hqc_meas.utils.pref_manifest import PreferencesManifest
    from hqc_meas.task_management.manager_manifest import TaskManagerManifest

    from hqc_meas.tasks.tasks_logic.views.loop_task_view\
        import LoopView

from ...util import process_app_events, close_all_windows


class TestLoopTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = LoopTask(task_name='Test')
        self.root.children_task.append(self.task)

    def test_task_handling(self):
        # Test adding removing a task.
        aux = PrintTask()
        self.task.task = aux

        # Check value is not written in database if a task is present.
        assert_not_in('value', self.task.task_database_entries)
        # Confirm the child was added (_child_added called)
        assert_is(aux.root_task, self.root)

        del self.task.task

        # Check value is written in database if no task is present.
        assert_in('value', self.task.task_database_entries)
        # Confirm the child was added (_child_removed called)
        assert_is(aux.root_task, None)

    def test_timing_handling(self):
        # Test enabling/disabling the timing.
        assert_not_in('elapsed_time', self.task.task_database_entries)

        self.task.timing = True

        assert_in('elapsed_time', self.task.task_database_entries)

        self.task.timing = False

        assert_not_in('elapsed_time', self.task.task_database_entries)

    def test_check_linspace_interface1(self):
        # Simply test that everything is ok when all formulas are true.
        interface = LinspaceLoopInterface()
        interface.start = '1.0'
        interface.stop = '2.0'
        interface.step = '0.1'
        self.task.interface = interface

        test, traceback = self.task.check()
        assert_true(test)
        assert_false(traceback)
        assert_equal(self.task.get_from_database('Test_point_number'), 11)

#    def test_check_linspace_interface2(self):
#        # Test handling a wrong start.
#        interface = LinspaceLoopInterface()
#        interface.start = '1.0'
#        interface.stop = '2.0'
#        interface.step = '0.1'
#        self.task.interface = interface
#
#        test, traceback = self.task.check(test_instr=True)
#        assert_true(test)
#        assert_false(traceback)
#
#    def test_check_linspace_interface3(self):
#        # Test handling a wrong stop.
#        interface = LinspaceLoopInterface()
#        interface.start = '1.0'
#        interface.stop = '2.0'
#        interface.step = '0.1'
#        self.task.interface = interface
#
#        test, traceback = self.task.check(test_instr=True)
#        assert_true(test)
#        assert_false(traceback)
#
#    def test_check_linspace_interface4(self):
#        # Test handling a wrong step.
#        interface = LinspaceLoopInterface()
#        interface.start = '1.0'
#        interface.stop = '2.0'
#        interface.step = '0.1'
#        self.task.interface = interface
#
#        test, traceback = self.task.check(test_instr=True)
#        assert_true(test)
#        assert_false(traceback)
#
#    def test_check_linspace_interface5(self):
#        # Test handling a wrong number of point.
#        interface = LinspaceLoopInterface()
#        interface.start = '1.0'
#        interface.stop = '2.0'
#        interface.step = '0.1'
#        self.task.interface = interface
#
#        test, traceback = self.task.check(test_instr=True)
#        assert_true(test)
#        assert_false(traceback)
#
#    def test_check_iterable_interface1(self):
#        # Simply test that everything is ok when all formulas are true.
#        self.task.interface = interface
#        self.task.target_value = '1.0'
#
#        profile = {'Test1': ({'defined_channels': [[1]]},
#                             {})}
#        self.root.run_time['profiles'] = profile
#
#        test, traceback = self.task.check(test_instr=True)
#        assert_true(test)
#        assert_false(traceback)
#
#    def test_check_iterable_interface2(self):
#        # Test handling a wrong iterable formula.
#        self.task.interface = interface
#        self.task.target_value = '1.0'
#
#        profile = {'Test1': ({'defined_channels': [[1]]},
#                             {})}
#        self.root.run_time['profiles'] = profile
#
#        test, traceback = self.task.check(test_instr=True)
#        assert_true(test)
#        assert_false(traceback)
#
#    def test_check_iterable_interface3(self):
#        # Test handling a wrong iterable type.
#        self.task.interface = interface
#        self.task.target_value = '1.0'
#
#        profile = {'Test1': ({'defined_channels': [[1]]},
#                             {})}
#        self.root.run_time['profiles'] = profile
#
#        test, traceback = self.task.check(test_instr=True)
#        assert_true(test)
#        assert_false(traceback)
#
#    def test_perform(self):
#        self.task.target_value = '1.0'
#
#        self.root.run_time['profiles'] = {'Test1': ({'voltage': [0.0],
#                                                     'funtion': ['VOLT'],
#                                                     'owner': [None]}, {})}
#
#        self.root.task_database.prepare_for_running()
#
#        self.task.perform()
#        assert_equal(self.root.get_from_database('Test_voltage'), 1.0)
#
#    def test_perform_task(self):
#        self.task.target_value = '1.0'
#
#        self.root.run_time['profiles'] = {'Test1': ({'voltage': [0.0],
#                                                     'funtion': ['VOLT'],
#                                                     'owner': [None]}, {})}
#
#        self.root.task_database.prepare_for_running()
#
#        self.task.perform()
#        assert_equal(self.root.get_from_database('Test_voltage'), 1.0)
#
#    def test_perform_timing(self):
#        self.task.target_value = '1.0'
#
#        self.root.run_time['profiles'] = {'Test1': ({'voltage': [0.0],
#                                                     'funtion': ['VOLT'],
#                                                     'owner': [None]}, {})}
#
#        self.root.task_database.prepare_for_running()
#
#        self.task.perform()
#        assert_equal(self.root.get_from_database('Test_voltage'), 1.0)
#
#    def test_perform_task_timing(self):
#        self.task.target_value = '1.0'
#
#        self.root.run_time['profiles'] = {'Test1': ({'voltage': [0.0],
#                                                     'funtion': ['VOLT'],
#                                                     'owner': [None]}, {})}
#
#        self.root.task_database.prepare_for_running()
#
#        self.task.perform()
#        assert_equal(self.root.get_from_database('Test_voltage'), 1.0)
#
#
#@attr('ui')
#class TestLoopView(object):
#
#    def setup(self):
#        self.workbench = Workbench()
#        self.workbench.register(CoreManifest())
#        self.workbench.register(StateManifest())
#        self.workbench.register(PreferencesManifest())
#        self.workbench.register(InstrManagerManifest())
#        self.workbench.register(TaskManagerManifest())
#
#        self.root = RootTask(should_stop=Event(), should_pause=Event())
#        self.task = SetDCVoltageTask(task_name='Test')
#        self.root.children_task.append(self.task)
#        self.root.run_time['drivers'] = {'Test': InstrHelper}
#
#        self.task.back_step = 0.1
#        self.task.delay = 0.1
#
#    def teardown(self):
#        close_all_windows()
#
#        self.workbench.unregister(u'hqc_meas.task_manager')
#        self.workbench.unregister(u'hqc_meas.instr_manager')
#        self.workbench.unregister(u'hqc_meas.preferences')
#        self.workbench.unregister(u'hqc_meas.state')
#        self.workbench.unregister(u'enaml.workbench.core')
#
#    def test_view1(self):
#        # Intantiate a view with no selected interface and select one after
#        window = enaml.widgets.api.Window()
#        core = self.workbench.get_plugin('enaml.workbench.core')
#        view = SetDcVoltageView(window, task=self.task, core=core)
#        window.show()
#
#        process_app_events()
#
#        assert_in('YokogawaGS200', view.drivers)
#        self.task.selected_driver = 'YokogawaGS200'
#        process_app_events()
#        assert_is(self.task.interface, None)
#
#        assert_in('TinyBilt', view.drivers)
#        self.task.selected_driver = 'TinyBilt'
#        process_app_events()
#        assert_is_instance(self.task.interface,
#                           MultiChannelVoltageSourceInterface)
#
#    def test_view2(self):
#        # Intantiate a view with a selected interface.
#        interface = MultiChannelVoltageSourceInterface(task=self.task)
#        self.task.interface = interface
#        self.task.target_value = '1.0'
#        self.task.selected_driver = 'TinyBilt'
#
#        interface = self.task.interface
#
#        window = enaml.widgets.api.Window()
#        core = self.workbench.get_plugin('enaml.workbench.core')
#        SetDcVoltageView(window, task=self.task, core=core)
#        window.show()
#
#        process_app_events()
#
#        assert_is(self.task.interface, interface)
