# -*- coding: utf-8 -*-
# =============================================================================
# module : Test_loop_task.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from nose.tools import (assert_equal, assert_true, assert_false, assert_in,
                        assert_not_equal, assert_is, assert_not_in,
                        assert_is_instance)
from nose.plugins.attrib import attr
from multiprocessing import Event
from enaml.workbench.api import Workbench

from hqc_meas.tasks.api import RootTask
from hqc_meas.tasks.tasks_logic.loop_task import LoopTask
from hqc_meas.tasks.tasks_logic.loop_iterable_interface\
    import IterableLoopInterface
from hqc_meas.tasks.tasks_logic.loop_linspace_interface\
    import LinspaceLoopInterface
from hqc_meas.tasks.tasks_logic.loop_exceptions_tasks\
    import BreakTask, ContinueTask

import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state.manifest import StateManifest
    from hqc_meas.utils.preferences.manifest import PreferencesManifest
    from hqc_meas.tasks.manager.manifest import TaskManagerManifest

    from hqc_meas.tasks.tasks_logic.views.loop_task_view\
        import LoopView

from ...util import process_app_events, close_all_windows
from ..testing_utilities import CheckTask


class TestLoopTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = LoopTask(task_name='Test')
        self.root.children_task.append(self.task)

    def test_task_handling(self):
        # Test adding removing a task.
        aux = CheckTask()
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

    def test_check_linspace_interface2(self):
        # Test handling a wrong start.
        interface = LinspaceLoopInterface()
        interface.start = '1.0*'
        interface.stop = '2.0'
        interface.step = '0.1'
        self.task.interface = interface

        test, traceback = self.task.check(test_instr=True)
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test-start', traceback)

    def test_check_linspace_interface3(self):
        # Test handling a wrong stop.
        interface = LinspaceLoopInterface()
        interface.start = '1.0'
        interface.stop = '2.0*'
        interface.step = '0.1'
        self.task.interface = interface

        test, traceback = self.task.check(test_instr=True)
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test-stop', traceback)

    def test_check_linspace_interface4(self):
        # Test handling a wrong step.
        interface = LinspaceLoopInterface()
        interface.start = '1.0'
        interface.stop = '2.0'
        interface.step = '0.1*'
        self.task.interface = interface

        test, traceback = self.task.check(test_instr=True)
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test-step', traceback)

    def test_check_linspace_interface5(self):
        # Test handling a wrong number of point.
        interface = LinspaceLoopInterface()
        interface.start = '1.0'
        interface.stop = '2.0'
        interface.step = '0.0'
        self.task.interface = interface

        test, traceback = self.task.check(test_instr=True)
        assert_false(test)
        assert_equal(len(traceback), 2)
        assert_in('root/Test-points', traceback)
        assert_in('root/Test-linspace', traceback)

    def test_check_iterable_interface1(self):
        # Simply test that everything is ok when all formulas are true.
        interface = IterableLoopInterface()
        interface.iterable = 'range(11)'
        self.task.interface = interface

        test, traceback = self.task.check()
        assert_true(test)
        assert_false(traceback)
        assert_equal(self.task.get_from_database('Test_point_number'), 11)

    def test_check_iterable_interface2(self):
        # Test handling a wrong iterable formula.
        interface = IterableLoopInterface()
        interface.iterable = '*range(11)'
        self.task.interface = interface

        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test', traceback)

    def test_check_iterable_interface3(self):
        # Test handling a wrong iterable type.
        interface = IterableLoopInterface()
        interface.iterable = '1.0'
        self.task.interface = interface

        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test', traceback)

    def test_perform1(self):
        # Test performing a simple loop no timing. Iterable interface.
        interface = IterableLoopInterface()
        interface.iterable = 'range(11)'
        self.task.interface = interface

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_value'), 10)

    def test_perform2(self):
        # Test performing a simple loop no timing. Linspace interface.
        interface = LinspaceLoopInterface()
        interface.start = '1.0'
        interface.stop = '2.0'
        interface.step = '0.1'
        self.task.interface = interface

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_value'), 2.0)

    def test_perform3(self):
        # Test performing a simple loop no timing. Break.
        interface = IterableLoopInterface()
        interface.iterable = 'range(11)'
        self.task.interface = interface
        self.task.children_task.append(BreakTask(task_name='break',
                                                 condition='{Test_value} == 5')
                                       )

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_value'), 5)

    def test_perform4(self):
        # Test performing a simple loop no timing. Continue
        interface = IterableLoopInterface()
        interface.iterable = 'range(11)'
        self.task.interface = interface
        self.task.children_task.append(ContinueTask(task_name='break',
                                                    condition='True')
                                       )
        self.task.children_task.append(CheckTask(task_name='check'))

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_false(self.task.children_task[1].perform_called)

    def test_perform_task1(self):
        # Test performing a loop with an embedded task no timing.
        interface = IterableLoopInterface()
        interface.iterable = 'range(11)'
        self.task.interface = interface
        self.task.task = CheckTask(task_name='check')

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_index'), 11)
        assert_true(self.task.task.perform_called)
        assert_equal(self.task.task.perform_value, 10)

    def test_perform_task2(self):
        # Test performing a loop with an embedded task no timing. Break.
        interface = IterableLoopInterface()
        interface.iterable = 'range(11)'
        self.task.interface = interface
        self.task.task = CheckTask(task_name='check')
        self.task.children_task.append(BreakTask(task_name='break',
                                                 condition='{Test_index} == 6')
                                       )

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_index'), 6)
        assert_true(self.task.task.perform_called)
        assert_equal(self.task.task.perform_value, 5)

    def test_perform_task3(self):
        # Test performing a loop with an embedded task no timing. Continue.
        interface = IterableLoopInterface()
        interface.iterable = 'range(11)'
        self.task.interface = interface
        self.task.task = CheckTask(task_name='check')
        self.task.children_task.append(ContinueTask(task_name='break',
                                                    condition='True')
                                       )
        self.task.children_task.append(CheckTask(task_name='check'))

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_index'), 11)
        assert_true(self.task.task.perform_called)
        assert_equal(self.task.task.perform_value, 10)
        assert_false(self.task.children_task[1].perform_called)

    def test_perform_timing1(self):
        # Test performing a simple loop timing.
        interface = IterableLoopInterface()
        interface.iterable = 'range(11)'
        self.task.interface = interface
        self.task.timing = True

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_value'), 10)
        assert_not_equal(self.root.get_from_database('Test_elapsed_time'), 1.0)

    def test_perform_timing2(self):
        # Test performing a simple loop timing. Break
        interface = IterableLoopInterface()
        interface.iterable = 'range(11)'
        self.task.interface = interface
        self.task.timing = True
        self.task.children_task.append(BreakTask(task_name='break',
                                                 condition='{Test_value} == 0')
                                       )

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_value'), 0)
        assert_not_equal(self.root.get_from_database('Test_elapsed_time'), 1.0)

    def test_perform_timing3(self):
        # Test performing a simple loop timing. Continue
        interface = IterableLoopInterface()
        interface.iterable = 'range(11)'
        self.task.interface = interface
        self.task.timing = True
        self.task.children_task.append(ContinueTask(task_name='break',
                                                    condition='True')
                                       )
        self.task.children_task.append(CheckTask(task_name='check'))

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_false(self.task.children_task[1].perform_called)
        assert_not_equal(self.root.get_from_database('Test_elapsed_time'), 1.0)

    def test_perform_timing_task1(self):
        # Test performing a loop with an embedded task no timing.
        interface = IterableLoopInterface()
        interface.iterable = 'range(11)'
        self.task.interface = interface
        self.task.timing = True
        self.task.task = CheckTask(task_name='check')

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_index'), 11)
        assert_true(self.task.task.perform_called)
        assert_equal(self.task.task.perform_value, 10)
        assert_not_equal(self.root.get_from_database('Test_elapsed_time'), 1.0)

    def test_perform_timing_task2(self):
        # Test performing a loop with an embedded task no timing. Break.
        interface = IterableLoopInterface()
        interface.iterable = 'range(11)'
        self.task.interface = interface
        self.task.timing = True
        self.task.task = CheckTask(task_name='check')
        self.task.children_task.append(BreakTask(task_name='break',
                                                 condition='{Test_index} == 1')
                                       )

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_index'), 1)
        assert_true(self.task.task.perform_called)
        assert_equal(self.task.task.perform_value, 0)
        assert_not_equal(self.root.get_from_database('Test_elapsed_time'), 1.0)

    def test_perform_timing_task3(self):
        # Test performing a loop with an embedded task no timing. Continue.
        interface = IterableLoopInterface()
        interface.iterable = 'range(11)'
        self.task.interface = interface
        self.task.timing = True
        self.task.task = CheckTask(task_name='check')
        self.task.children_task.append(ContinueTask(task_name='break',
                                                    condition='True')
                                       )
        self.task.children_task.append(CheckTask(task_name='check'))

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_index'), 11)
        assert_true(self.task.task.perform_called)
        assert_equal(self.task.task.perform_value, 10)
        assert_false(self.task.children_task[1].perform_called)
        assert_not_equal(self.root.get_from_database('Test_elapsed_time'), 1.0)


@attr('ui')
class TestLoopView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = LoopTask(task_name='Test')
        self.root.children_task.append(self.task)

    def teardown(self):
        close_all_windows()

        self.workbench.unregister(u'hqc_meas.task_manager')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_view1(self):
        # Intantiate a view with no selected interface and select one after
        window = enaml.widgets.api.Window()
        core = self.workbench.get_plugin('enaml.workbench.core')
        view = LoopView(window, task=self.task, core=core)
        window.show()

        process_app_events()

        view.widgets()[1].selected = LinspaceLoopInterface
        process_app_events()
        assert_is_instance(self.task.interface, LinspaceLoopInterface)

        view.widgets()[1].selected = IterableLoopInterface
        process_app_events()
        assert_is_instance(self.task.interface, IterableLoopInterface)

    def test_view2(self):
        # Intantiate a view with a selected interface.
        interface = LinspaceLoopInterface()
        self.task.interface = interface

        window = enaml.widgets.api.Window()
        core = self.workbench.get_plugin('enaml.workbench.core')
        LoopView(window, task=self.task, core=core)
        window.show()

        process_app_events()

        assert_is(self.task.interface, interface)
