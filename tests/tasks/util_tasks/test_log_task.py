# -*- coding: utf-8 -*-
# =============================================================================
# module : test_log_task.py
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
from hqc_meas.tasks.tasks_util.log_task import LogTask

import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from hqc_meas.utils.pref_manifest import PreferencesManifest
    from hqc_meas.task_management.manager_manifest import TaskManagerManifest

    from hqc_meas.tasks.tasks_util.views.log_task_view import LogView

from ...util import process_app_events, close_all_windows


class TestLogTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = LogTask(task_name='Test')
        self.root.children_task.append(self.task)

    def test_check1(self):
        # Simply test that everything is ok message is evaluable.
        self.task.message = 'True'

        test, traceback = self.task.check()
        assert_true(test)
        assert_false(traceback)

    def test_check2(self):
        # Test handling a wrong message.
        self.task.message = 'True{'

        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test', traceback)

    def test_perform(self):
        # Test performing when condition is True.
        self.task.message = 'toro'

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_message'), 'toro')


@attr('ui')
class TestLogView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = LogTask(task_name='Test', message='rr')
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
        view = LogView(window, task=self.task)
        window.show()

        process_app_events()

        assert_equal(view.widgets()[1].text, 'rr')

        view.widgets()[1].text = 'test'
        process_app_events()
        assert_equal(self.task.message, 'test')
