# -*- coding: utf-8 -*-
# =============================================================================
# module : test_loop_exception_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from nose.tools import (assert_equal, assert_true, assert_false, assert_in,
                        istest, nottest)
from nose.plugins.attrib import attr
from multiprocessing import Event
from enaml.workbench.api import Workbench

from hqc_meas.tasks.api import RootTask
from hqc_meas.tasks.tasks_logic.loop_task import LoopTask
from hqc_meas.tasks.tasks_logic.while_task import WhileTask
from hqc_meas.tasks.tasks_logic.loop_exceptions_tasks\
    import BreakTask, ContinueTask

import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from hqc_meas.utils.pref_manifest import PreferencesManifest
    from hqc_meas.task_management.manager_manifest import TaskManagerManifest

    from hqc_meas.tasks.tasks_logic.views.loop_exceptions_views\
        import BreakView, ContinueView

from ...util import process_app_events, close_all_windows


@nottest
class BaseExceptionTest(object):

    excep_class = None

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = self.excep_class(task_name='Test')

    def test_check1(self):
        # Simply test that everything is ok condition is evaluable and parent
        # is a Loop.
        loop = LoopTask(children_task=[self.task])
        self.root.children_task.append(loop)
        self.task.condition = 'True'

        test, traceback = self.task.check()
        assert_true(test)
        assert_false(traceback)

    def test_check2(self):
        # Simply test that everything is ok condition is evaluable and parent
        # is a While.
        whil = WhileTask(children_task=[self.task])
        self.root.children_task.append(whil)
        self.task.condition = 'True'

        test, traceback = self.task.check()
        assert_true(test)
        assert_false(traceback)

    def test_check3(self):
        # Test handling a wrong condition.
        loop = LoopTask(task_name='Parent', children_task=[self.task])
        self.root.children_task.append(loop)
        self.task.condition = '*True'

        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Parent/Test-cond', traceback)

    def test_check4(self):
        # Test handling a wrong parent type.
        self.root.children_task.append(self.task)
        self.task.condition = 'True'

        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test-parent', traceback)


@istest
class TestBreakTask(BaseExceptionTest):

    excep_class = BreakTask


@istest
class TestContinueTask(BaseExceptionTest):

    excep_class = ContinueTask


@nottest
class BaseTestExceptionView(object):

    excep_class = None
    view_class = None

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = self.excep_class(task_name='Test', condition='rr')
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
        view = self.view_class(window, task=self.task)
        window.show()

        process_app_events()

        assert_equal(view.widgets()[1].text, 'rr')

        view.widgets()[1].text = 'test'
        process_app_events()
        assert_equal(self.task.condition, 'test')


@istest
@attr('ui')
class TestBreakView(BaseTestExceptionView):

    excep_class = BreakTask
    view_class = BreakView


@istest
@attr('ui')
class TestContinueView(BaseTestExceptionView):

    excep_class = ContinueTask
    view_class = ContinueView
