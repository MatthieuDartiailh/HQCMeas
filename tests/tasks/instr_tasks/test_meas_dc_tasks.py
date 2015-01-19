# -*- coding: utf-8 -*-
# =============================================================================
# module : test_meas_dc_voltage.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from nose.tools import (assert_equal)
from nose.plugins.attrib import attr
from multiprocessing import Event
from enaml.workbench.api import Workbench

from hqc_meas.tasks.api import RootTask
from hqc_meas.tasks.tasks_instr.meas_dc_tasks import MeasDCVoltageTask

import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state.manifest import StateManifest
    from hqc_meas.utils.preferences.manifest import PreferencesManifest
    from hqc_meas.tasks.manager.manifest import TaskManagerManifest
    from hqc_meas.instruments.manager.manifest import InstrManagerManifest

    from hqc_meas.tasks.tasks_instr.views.meas_dc_views\
        import DCVoltMeasView

from ...util import process_app_events, close_all_windows
from .instr_helper import InstrHelper


class TestSetDCVoltageTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = MeasDCVoltageTask(task_name='Test')
        self.root.children_task.append(self.task)
        self.root.run_time['drivers'] = {'Test': InstrHelper}

        # This is set simply to make sure the test of InstrTask pass.
        self.task.selected_driver = 'Test'
        self.task.selected_profile = 'Test1'

    def test_perform(self):
        self.task.wait_time = 1.0

        self.root.run_time['profiles'] = {'Test1': ({},
                                                    {'read_voltage_dc': [2.0]})
                                                    }

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_voltage'), 2.0)


@attr('ui')
class TestSetDCVoltageView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(InstrManagerManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = MeasDCVoltageTask(task_name='Test')
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
        view = DCVoltMeasView(window, task=self.task, core=core)
        window.show()

        process_app_events()
