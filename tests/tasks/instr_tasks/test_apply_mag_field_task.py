# -*- coding: utf-8 -*-
# =============================================================================
# module : test_apply_mag_field_task.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from nose.tools import (assert_equal, assert_true, assert_false, assert_in)
from nose.plugins.attrib import attr
from multiprocessing import Event
from enaml.workbench.api import Workbench

from hqc_meas.tasks.api import RootTask
from hqc_meas.tasks.tasks_instr.apply_mag_field_task import ApplyMagFieldTask

import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state.manifest import StateManifest
    from hqc_meas.utils.preferences.manifest import PreferencesManifest
    from hqc_meas.tasks.manager.manifest import TaskManagerManifest
    from hqc_meas.instruments.manager.manifest import InstrManagerManifest

    from hqc_meas.tasks.tasks_instr.views.apply_mag_field_view\
        import ApplyMagFieldView

from ...util import process_app_events, close_all_windows
from .instr_helper import InstrHelper
from ..testing_utilities import join_threads


class TestApplyMagFieldTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = ApplyMagFieldTask(task_name='Test')
        self.root.children_task.append(self.task)
        self.root.run_time['drivers'] = {'Test': InstrHelper}

        # This is set simply to make sure the test of InstrTask pass.
        self.task.selected_driver = 'Test'
        self.task.selected_profile = 'Test1'

    def test_check1(self):
        # Simply test that everything is ok if field can be evaluated.
        self.task.target_field = '3.0'

        test, traceback = self.task.check(test_instr=True)
        assert_true(test)
        assert_false(traceback)

        assert_equal(self.task.get_from_database('Test_Bfield'), 3.0)

    def test_check2(self):
        # Check handling a wrong field.
        self.task.target_field = '*1.0*'

        test, traceback = self.task.check(test_instr=True)
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test-field', traceback)

        assert_equal(self.task.get_from_database('Test_Bfield'), 0.01)

    def test_perform1(self):
        # Simple test when everything is right.
        self.task.target_field = '2.0'

        self.root.run_time['profiles'] = {'Test1': ({'owner': []},
                                                    {'make_ready': [None],
                                                     'go_to_field': [None]}
                                                    )}

        self.root.task_database.prepare_for_running()

        self.task.perform()
        join_threads(self.root)
        assert_equal(self.root.get_from_database('Test_Bfield'), 2.0)

    def test_perform2(self):
        # Test multiple run when connection is maintained.
        self.task.target_field = '2.0'

        self.root.run_time['profiles'] = {'Test1': ({'owner': []},
                                                    {'make_ready': [None],
                                                     'go_to_field': [None],
                                                     'check_connection': [True]
                                                     }
                                                    )}

        self.root.task_database.prepare_for_running()

        self.task.perform()
        join_threads(self.root)
        self.task.perform()
        join_threads(self.root)
        # In case of fail make_ready would be called twice.
        assert_equal(self.root.get_from_database('Test_Bfield'), 2.0)


@attr('ui')
class TestApplyMagFieldView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(InstrManagerManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = ApplyMagFieldTask(task_name='Test')
        self.root.children_task.append(self.task)
        self.root.run_time['drivers'] = {'Test': InstrHelper}

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
        view = ApplyMagFieldView(window, task=self.task, core=core)
        window.show()

        process_app_events()
