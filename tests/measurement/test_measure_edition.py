# -*- coding: utf-8 -*-
# =============================================================================
# module : test_measure_edition.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from enaml.workbench.api import Workbench
import enaml
from nose.tools import (assert_not_in)

from hqc_meas.measurement.measure import Measure
from hqc_meas.tasks.base_tasks import RootTask

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from enaml.workbench.ui.ui_manifest import UIManifest
    from hqc_meas.app_manifest import HqcAppManifest
    from hqc_meas.utils.state.manifest import StateManifest
    from hqc_meas.utils.preferences.manifest import PreferencesManifest
    from hqc_meas.utils.log.manifest import LogManifest
    from hqc_meas.utils.dependencies.manifest import DependenciesManifest
    from hqc_meas.measurement.manifest import MeasureManifest
    from hqc_meas.tasks.manager.manifest import TaskManagerManifest
    from hqc_meas.instruments.manager.manifest import InstrManagerManifest
    from hqc_meas.measurement.measure_edition import MeasureEditorDialog

    from .helpers import TestSuiteManifest

from ..util import (complete_line, process_app_events, close_all_windows)


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


class TestMeasureSpace(object):

    test_dir = ''

    @classmethod
    def setup_class(cls):
        print complete_line(__name__ +
                            ':{}.setup_class()'.format(cls.__name__), '-', 77)

    @classmethod
    def teardown_class(cls):
        print complete_line(__name__ +
                            ':{}.teardown_class()'.format(cls.__name__), '-',
                            77)

    def setup(self):

        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(UIManifest())
        self.workbench.register(HqcAppManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(LogManifest())
        self.workbench.register(DependenciesManifest())
        self.workbench.register(TaskManagerManifest())
        self.workbench.register(InstrManagerManifest())
        self.workbench.register(MeasureManifest())
        self.workbench.register(TestSuiteManifest())

    def teardown(self):
        close_all_windows()
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        core.invoke_command(u'enaml.workbench.ui.close_workspace', {}, self)
        self.workbench.unregister(u'tests.suite')
        self.workbench.unregister(u'hqc_meas.measure')
        self.workbench.unregister(u'hqc_meas.task_manager')
        self.workbench.unregister(u'hqc_meas.instr_manager')
        self.workbench.unregister(u'hqc_meas.dependencies')
        self.workbench.unregister(u'hqc_meas.logging')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'hqc_meas.app')
        self.workbench.unregister(u'enaml.workbench.ui')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_measure_editor_dialog1(self):
        # Test that the build_deps are correctly destroyed when closing.
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.measure.workspace'},
                            self)
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')

        measure = Measure(plugin=plugin, name='Test')
        measure.root_task = RootTask()
        measure.store['build_deps'] = 25

        ed = MeasureEditorDialog(measure=measure, workspace=plugin.workspace)
        ed.show()
        process_app_events()
        ed.close()
        process_app_events()
        assert_not_in('build_deps', measure.store)
        close_all_windows()

    def test_measure_editor_dialog2(self):
        # Test that everything goes well in the absence of build_deps
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.measure.workspace'},
                            self)
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')

        measure = Measure(plugin=plugin, name='Test')
        measure.root_task = RootTask()

        ed = MeasureEditorDialog(measure=measure, workspace=plugin.workspace)
        ed.show()
        process_app_events()
        ed.close()
        process_app_events()
        assert_not_in('build_deps', measure.store)
        close_all_windows()
