# -*- coding: utf-8 -*-
# =============================================================================
# module : test_meas_dc_voltage.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from nose.tools import (assert_equal, assert_not_in)
from nose.plugins.attrib import attr
from multiprocessing import Event
from enaml.workbench.api import Workbench

from hqc_meas.tasks.api import RootTask
from hqc_meas.tasks.tasks_instr.lock_in_measure_task import LockInMeasureTask

import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state.manifest import StateManifest
    from hqc_meas.utils.preferences.manifest import PreferencesManifest
    from hqc_meas.tasks.manager.manifest import TaskManagerManifest
    from hqc_meas.instruments.manager.manifest import InstrManagerManifest

    from hqc_meas.tasks.tasks_instr.views.lock_in_meas_view\
        import LockInMeasView

from ...util import process_app_events, close_all_windows
from .instr_helper import InstrHelper


class TestSetDCVoltageTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = LockInMeasureTask(task_name='Test')
        self.root.children_task.append(self.task)
        self.root.run_time['drivers'] = {'Test': InstrHelper}

        # This is set simply to make sure the test of InstrTask pass.
        self.task.selected_driver = 'Test'
        self.task.selected_profile = 'Test1'

    def test_mode_observation(self):
        # Check database is correctly updated when the mode change.
        self.task.mode = 'X'

        assert_equal(self.task.get_from_database('Test_x'), 1.0)
        aux = self.task.accessible_database_entries()
        assert_not_in('Test_y', aux)
        assert_not_in('Test_amplitude', aux)
        assert_not_in('Test_phase', aux)

        self.task.mode = 'Y'

        assert_equal(self.task.get_from_database('Test_y'), 1.0)
        aux = self.task.accessible_database_entries()
        assert_not_in('Test_x', aux)
        assert_not_in('Test_amplitude', aux)
        assert_not_in('Test_phase', aux)

        self.task.mode = 'X&Y'

        assert_equal(self.task.get_from_database('Test_x'), 1.0)
        assert_equal(self.task.get_from_database('Test_y'), 1.0)
        aux = self.task.accessible_database_entries()
        assert_not_in('Test_amplitude', aux)
        assert_not_in('Test_phase', aux)

        self.task.mode = 'Amp'

        assert_equal(self.task.get_from_database('Test_amplitude'), 1.0)
        aux = self.task.accessible_database_entries()
        assert_not_in('Test_x', aux)
        assert_not_in('Test_y', aux)
        assert_not_in('Test_phase', aux)

        self.task.mode = 'Phase'

        assert_equal(self.task.get_from_database('Test_phase'), 1.0)
        aux = self.task.accessible_database_entries()
        assert_not_in('Test_x', aux)
        assert_not_in('Test_y', aux)
        assert_not_in('Test_amplitude', aux)

        self.task.mode = 'Amp&Phase'

        assert_equal(self.task.get_from_database('Test_amplitude'), 1.0)
        assert_equal(self.task.get_from_database('Test_phase'), 1.0)
        aux = self.task.accessible_database_entries()
        assert_not_in('Test_x', aux)
        assert_not_in('Test_y', aux)

    def test_perform1(self):
        self.task.mode = 'X'

        self.root.run_time['profiles'] = {'Test1': ({}, {'read_x': [2.0]})}

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_x'), 2.0)

    def test_perform2(self):
        self.task.mode = 'Y'

        self.root.run_time['profiles'] = {'Test1': ({}, {'read_y': [2.0]})}

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_y'), 2.0)

    def test_perform3(self):
        self.task.mode = 'X&Y'

        self.root.run_time['profiles'] = {'Test1': ({},
                                                    {'read_xy': [(2.0, 3.0)]})}

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_x'), 2.0)
        assert_equal(self.root.get_from_database('Test_y'), 3.0)

    def test_perform4(self):
        self.task.mode = 'Amp'

        self.root.run_time['profiles'] = {'Test1': ({},
                                                    {'read_amplitude': [2.0]})}

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_amplitude'), 2.0)

    def test_perform5(self):
        self.task.mode = 'Phase'

        self.root.run_time['profiles'] = {'Test1': ({}, {'read_phase': [2.0]})}

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_phase'), 2.0)

    def test_perform6(self):
        self.task.mode = 'Amp&Phase'

        self.root.run_time['profiles'] = {'Test1': ({},
                                          {'read_amp_and_phase': [(2.0, 3.0)]})
                                          }

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_amplitude'), 2.0)
        assert_equal(self.root.get_from_database('Test_phase'), 3.0)


@attr('ui')
class TestLockInView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(InstrManagerManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = LockInMeasureTask(task_name='Test')
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
        view = LockInMeasView(window, task=self.task, core=core)
        window.show()

        process_app_events()
