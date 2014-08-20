# -*- coding: utf-8 -*-
# =============================================================================
# module : test_formula_task.py
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

from hqc_meas.tasks.api import RootTask
from hqc_meas.tasks.tasks_util.formula_task import FormulaTask

import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from hqc_meas.utils.pref_manifest import PreferencesManifest
    from hqc_meas.task_management.manager_manifest import TaskManagerManifest

    from hqc_meas.tasks.tasks_util.views.formula_view import FormulaView

from ...util import process_app_events, close_all_windows


class TestFormulaTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = FormulaTask(task_name='Test')
        self.root.children_task.append(self.task)

    def test_formulas_observation(self):
        # Test that the database is correctly updated when defs change.
        self.task.formulas = [('1', '2.0'), ('2', "['a', 1.0]")]

        assert_equal(self.task.get_from_database('Test_1'), 1.0)
        assert_equal(self.task.get_from_database('Test_2'), 1.0)

        self.task.formulas = []

        aux = self.task.accessible_database_entries()
        assert_not_in('Test_1', aux)
        assert_not_in('Test_2', aux)

    def test_check1(self):
        # Simply test that everything is ok if formulas are corrects.
        self.task.formulas = [('1', '2.0'), ('2', "['a', 1.0]")]

        test, traceback = self.task.check()
        assert_true(test)
        assert_false(traceback)
        assert_equal(self.task.get_from_database('Test_1'), 2.0)
        assert_equal(self.task.get_from_database('Test_2'), ['a', 1.0])

    def test_check2(self):
        # Test handling a wrong formula.
        self.task.formulas = [('1', '2.0'), ('2', "*['a', 1.0]")]

        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test-2', traceback)
        assert_equal(self.task.get_from_database('Test_1'), 2.0)
        assert_equal(self.task.get_from_database('Test_2'), 1.0)

    def test_perform(self):
        # Test performing.
        self.task.formulas = [('1', '2.0'), ('2', "['a', 1.0]")]

        self.root.task_database.prepare_for_running()

        self.task.perform()

        assert_equal(self.task.get_from_database('Test_1'), 2.0)
        assert_equal(self.task.get_from_database('Test_2'), ['a', 1.0])


@attr('ui')
class TestFormulaView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = FormulaTask(task_name='Test')
        self.root.children_task.append(self.task)

    def teardown(self):
        close_all_windows()

        self.workbench.unregister(u'hqc_meas.task_manager')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_view(self):
        # Intantiate a view.
        window = enaml.widgets.api.Window()
        FormulaView(window, task=self.task)
        window.show()

        process_app_events()

        self.task.formulas = [('1', '2.0'), ('2', "*['a', 1.0]")]

        process_app_events()
