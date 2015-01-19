# -*- coding: utf-8 -*-
# =============================================================================
# module : test_while_task.py
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
from hqc_meas.tasks.tasks_logic.while_task import WhileTask

import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state.manifest import StateManifest
    from hqc_meas.utils.preferences.manifest import PreferencesManifest
    from hqc_meas.tasks.manager.manifest import TaskManagerManifest

    from hqc_meas.tasks.tasks_logic.views.while_task_view\
        import WhileView

from ...util import process_app_events, close_all_windows
from ..testing_utilities import CheckTask


class TestWhileTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = WhileTask(task_name='Test')
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
        self.task.condition = '{Test_index} < 5'

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.check.perform_called, 4)

    def test_perform2(self):
        # Test performing when condition is False.
        self.task.condition = '1 < 0'

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_false(self.check.perform_called)

    def test_perform3(self):
        # Test performing when condition is True. Stop event set.
        self.root.should_stop.set()
        self.task.condition = '{Test_index} < 5'

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.check.perform_called, 0)


@attr('ui')
class TestWhileView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = WhileTask(task_name='Test', condition='rr')
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
        view = WhileView(window, task=self.task, core=core)
        window.show()

        process_app_events()

        assert_equal(view.widgets()[1].text, 'rr')

        view.widgets()[1].text = 'test'
        process_app_events()
        assert_equal(self.task.condition, 'test')
