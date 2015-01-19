# -*- coding: utf-8 -*-
# =============================================================================
# module : test_array_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from nose.tools import (assert_equal, assert_true, assert_false, assert_in,
                        assert_not_in)
from nose.plugins.attrib import attr
from multiprocessing import Event
from enaml.workbench.api import Workbench
import numpy as np

from hqc_meas.tasks.api import RootTask
from hqc_meas.tasks.tasks_util.array_tasks import (ArrayExtremaTask,
                                                   ArrayFindValueTask)

import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state.manifest import StateManifest
    from hqc_meas.utils.preferences.manifest import PreferencesManifest
    from hqc_meas.tasks.manager.manifest import TaskManagerManifest

    from hqc_meas.tasks.tasks_util.views.array_views\
        import ArrayExtremaView, ArrayFindValueView

from ...util import process_app_events, close_all_windows


class TestArrayExtremaTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = ArrayExtremaTask(task_name='Test')
        self.root.children_task.append(self.task)
        array = np.zeros((5,), dtype=[('var1', 'f8'), ('var2', 'f8')])
        array['var1'][1] = -1
        array['var1'][3] = 1
        self.root.write_in_database('array', array)

    def test_mode_observation(self):
        # Check database is correctly updated when the mode change.
        self.task.mode = 'Min'

        assert_equal(self.task.get_from_database('Test_min_ind'), 0)
        assert_equal(self.task.get_from_database('Test_min_value'), 1.0)
        aux = self.task.accessible_database_entries()
        assert_not_in('Test_max_ind', aux)
        assert_not_in('Test_max_value', aux)

        self.task.mode = 'Max'

        assert_equal(self.task.get_from_database('Test_max_ind'), 0)
        assert_equal(self.task.get_from_database('Test_max_value'), 2.0)
        aux = self.task.accessible_database_entries()
        assert_not_in('Test_min_ind', aux)
        assert_not_in('Test_min_value', aux)

        self.task.mode = 'Max & min'

        assert_equal(self.task.get_from_database('Test_min_ind'), 0)
        assert_equal(self.task.get_from_database('Test_min_value'), 1.0)
        assert_equal(self.task.get_from_database('Test_max_ind'), 0)
        assert_equal(self.task.get_from_database('Test_max_value'), 2.0)

    def test_check1(self):
        # Simply test that everything is ok if the array exists in the database
        self.root.write_in_database('array', np.zeros((5,)))
        self.task.target_array = '{Root_array}'

        test, traceback = self.task.check()
        assert_true(test)
        assert_false(traceback)

    def test_check2(self):
        # Simply test that everything is ok if the array exists in the database
        # and the column name is ok.
        self.task.target_array = '{Root_array}'
        self.task.column_name = 'var1'

        test, traceback = self.task.check()
        assert_true(test)
        assert_false(traceback)

    def test_check3(self):
        # Test handling a wrong array name.
        self.task.target_array = '*{Root_array}'
        self.task.column_name = 'var3'

        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test', traceback)

    def test_check4(self):
        # Test handling an array without names when a name is given.
        self.root.write_in_database('array', np.zeros((5,)))
        self.task.target_array = '{Root_array}'
        self.task.column_name = 'var1'

        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test', traceback)

    def test_check5(self):
        # Test handling an array with names when no name is given.
        self.task.target_array = '{Root_array}'

        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test', traceback)

    def test_check6(self):
        # Test handling a wrong column name.
        self.task.target_array = '{Root_array}'
        self.task.column_name = 'var3'

        test, traceback = self.task.check()
        assert_true(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test', traceback)

    def test_check7(self):
        # Test handling a 2d array without names.
        self.task.target_array = '{Root_array}'

        array = np.zeros((5, 5))
        self.root.write_in_database('array', array)

        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test', traceback)

    def test_perform1(self):
        # Test performing when mode is 'Max'.
        self.task.mode = 'Max'
        self.task.target_array = '{Root_array}'
        self.task.column_name = 'var1'
        self.root.task_database.prepare_for_running()

        self.task.perform()

        assert_equal(self.task.get_from_database('Test_max_ind'), 3)
        assert_equal(self.task.get_from_database('Test_max_value'), 1.0)

    def test_perform2(self):
        # Test performing when mode is 'Min'.
        self.task.mode = 'Min'
        self.task.target_array = '{Root_array}'
        self.task.column_name = 'var1'
        self.root.task_database.prepare_for_running()

        self.task.perform()

        assert_equal(self.task.get_from_database('Test_min_ind'), 1)
        assert_equal(self.task.get_from_database('Test_min_value'), -1.0)

    def test_perform3(self):
        # Test performing when mode is 'Max & min'.
        self.task.mode = 'Max & min'
        self.task.target_array = '{Root_array}'
        self.task.column_name = 'var1'
        self.root.task_database.prepare_for_running()

        self.task.perform()

        assert_equal(self.task.get_from_database('Test_max_ind'), 3)
        assert_equal(self.task.get_from_database('Test_max_value'), 1.0)
        assert_equal(self.task.get_from_database('Test_min_ind'), 1)
        assert_equal(self.task.get_from_database('Test_min_value'), -1.0)

    def test_perform4(self):
        # Test performing when no column name is given.
        self.root.write_in_database('array', np.zeros((5,)))
        self.task.mode = 'Max'
        self.task.target_array = '{Root_array}'
        self.root.task_database.prepare_for_running()

        self.task.perform()

        assert_equal(self.task.get_from_database('Test_max_ind'), 0)
        assert_equal(self.task.get_from_database('Test_max_value'), 0.0)


@attr('ui')
class TestArrayExtremaView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = ArrayExtremaTask(task_name='Test')
        self.root.children_task.append(self.task)

    def teardown(self):
        close_all_windows()

        self.workbench.unregister(u'hqc_meas.task_manager')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_view(self):
        # Intantiate a view with no selected interface and select one after
        window = enaml.widgets.api.Window()
        view = ArrayExtremaView(window, task=self.task)
        window.show()

        process_app_events()


class TestArrayFindValueTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = ArrayFindValueTask(task_name='Test')
        self.root.children_task.append(self.task)
        array = np.zeros((5,), dtype=[('var1', 'f8'), ('var2', 'f8')])
        array['var1'][1] = -1.5
        array['var1'][3] = 1.6359
        array['var1'][4] = 1.6359
        self.root.write_in_database('array', array)

    def test_check1(self):
        # Simply test that everything is ok if the array exists in the database
        # and value can be evaluated.
        self.root.write_in_database('array', np.zeros((5,)))
        self.task.target_array = '{Root_array}'
        self.task.value = '1.6359'

        test, traceback = self.task.check()
        assert_true(test)
        assert_false(traceback)

    def test_check2(self):
        # Simply test that everything is ok if the array exists in the database
        # the column name is ok, and value can be evaluated.
        self.task.target_array = '{Root_array}'
        self.task.column_name = 'var1'
        self.task.value = '1.6359'

        test, traceback = self.task.check()
        assert_true(test)
        assert_false(traceback)

    def test_check3(self):
        # Test handling a wrong array name.
        self.task.target_array = '*{Root_array}'
        self.task.column_name = 'var3'
        self.task.value = '1.6359'

        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test-array', traceback)

    def test_check4(self):
        # Test handling an array without names when a name is given.
        self.root.write_in_database('array', np.zeros((5,)))
        self.task.target_array = '{Root_array}'
        self.task.column_name = 'var1'
        self.task.value = '1.6359'

        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test-column', traceback)

    def test_check5(self):
        # Test handling an array with names when no name is given.
        self.task.target_array = '{Root_array}'
        self.task.value = '1.6359'

        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test-column', traceback)

    def test_check6(self):
        # Test handling a wrong column name.
        self.task.target_array = '{Root_array}'
        self.task.column_name = 'var3'
        self.task.value = '1.6359'

        test, traceback = self.task.check()
        assert_true(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test-column', traceback)

    def test_check7(self):
        # Test handling a wrong value.
        self.task.target_array = '{Root_array}'
        self.task.column_name = 'var1'
        self.task.value = '*1.6359'

        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test-value', traceback)

    def test_check8(self):
        # Test handling a 2d array value.
        self.task.target_array = '{Root_array}'
        self.task.value = '1.6359'

        array = np.zeros((5, 5))
        self.root.write_in_database('array', array)

        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test-dim', traceback)

    def test_perform1(self):
        # Test performing when mode is 'Max'.
        self.task.value = '1.6359'
        self.task.target_array = '{Root_array}'
        self.task.column_name = 'var1'
        self.root.task_database.prepare_for_running()

        self.task.perform()

        assert_equal(self.task.get_from_database('Test_index'), 3)


@attr('ui')
class TestArrayFindValueView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = ArrayFindValueTask(task_name='Test')
        self.root.children_task.append(self.task)

    def teardown(self):
        close_all_windows()

        self.workbench.unregister(u'hqc_meas.task_manager')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_view(self):
        # Intantiate a view with no selected interface and select one after
        window = enaml.widgets.api.Window()
        view = ArrayFindValueView(window, task=self.task)
        window.show()

        process_app_events()
