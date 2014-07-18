# -*- coding: utf-8 -*-
# =============================================================================
# module : test_conditional_task.py
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
from hqc_meas.tasks.tasks_logic.conditional_task import ConditionalTask

import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from hqc_meas.utils.pref_manifest import PreferencesManifest
    from hqc_meas.task_management.manager_manifest import TaskManagerManifest

    from hqc_meas.tasks.tasks_logic.views.conditional_task_view\
        import ConditionalView

from ...util import process_app_events, close_all_windows
from ..testing_utilities import CheckTask


class TestConditionTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = ConditionalTask(task_name='Test')
        self.root.children_task.append(self.task)
        self.check = CheckTask(task_name='check')
        self.task.children_task.append(self.check)

    def test_check1(self):
        # Simply test that everything is ok condition is evaluable.
        self.task.condition = 'True'

        test, traceback = self.task.check()
        assert_true(test)
        assert_false(traceback)
        assert_true(self.check.check_called)

    def test_check2(self):
        # Test handling a wrong condition.
        self.task.condition = '*True'

        test, traceback = self.task.check(test_instr=True)
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test-cond', traceback)

    def test_perform1(self):
        # Test performing when condition is True.
        self.task.condition = 'True'

        self.task.perform()
        assert_true(self.check.perform_called)

    def test_perform2(self):
        # Test performing when condition is False.
        self.task.condition = '1 < 0'

        self.task.perform()
        assert_false(self.check.perform_called)


@attr('ui')
class TestConditionalView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = ConditionalTask(task_name='Test', condition='rr')
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
        core = self.workbench.get_plugin('enaml.workbench.core')
        view = ConditionalView(window, task=self.task, core=core)
        window.show()

        process_app_events()

        assert_equal(view.widgets()[1].text, 'rr')

        view.widgets()[1].text = 'test'
        process_app_events()
        assert_equal(self.task.condition, 'test')
