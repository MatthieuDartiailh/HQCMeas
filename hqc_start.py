# -*- coding: utf-8 -*-
# =============================================================================
# module : hqc_start.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from enaml.workbench.api import Workbench
import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from enaml.workbench.ui.ui_manifest import UIManifest
    from hqc_meas.app_manifest import HqcAppManifest
    from hqc_meas.utils.pref_manifest import PreferencesManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from hqc_meas.measurement.manifest import MeasureManifest
    from hqc_meas.task_management.manager_manifest import TaskManagerManifest
    from hqc_meas.instruments.manager_manifest import InstrManagerManifest
    from hqc_meas.log_system.log_manifest import LogManifest
    from hqc_meas.debug.debugger_manifest import DebuggerManifest

if __name__ == '__main__':

    WORKSPACES = {'measure': 'hqc_meas.measure.workspace',
                  'debug': 'hqc_meas.debug.workspace'}

    import argparse
    parser = argparse.ArgumentParser(description='Start the Hqc app')
    parser.add_argument("-w", "--workspace", help='select start-up workspace',
                        default='measure', choices=WORKSPACES)
    args = parser.parse_args()

    workbench = Workbench()
    workbench.register(CoreManifest())
    workbench.register(UIManifest())
    workbench.register(HqcAppManifest())
    workbench.register(StateManifest())
    workbench.register(PreferencesManifest())
    workbench.register(LogManifest())
    workbench.register(TaskManagerManifest())
    workbench.register(InstrManagerManifest())
    workbench.register(MeasureManifest())
    workbench.register(DebuggerManifest())

    core = workbench.get_plugin('enaml.workbench.core')
    core.invoke_command('hqc_meas.logging.start_logging', {}, workbench)
    core.invoke_command('enaml.workbench.ui.select_workspace',
                        {'workspace': WORKSPACES[args.workspace]}, workbench)

    ui = workbench.get_plugin(u'enaml.workbench.ui')
    ui.show_window()
    ui.window.maximize()
    ui.start_application()

    workbench.unregister(u'hqc_meas.debug')
    workbench.unregister(u'hqc_meas.measure')
    workbench.unregister(u'hqc_meas.task_manager')
    workbench.unregister(u'hqc_meas.instr_manager')
    workbench.unregister(u'hqc_meas.logging')
    workbench.unregister(u'hqc_meas.preferences')
    workbench.unregister(u'hqc_meas.state')
    workbench.unregister(u'hqc_meas.app')
    workbench.unregister(u'enaml.workbench.ui')
    workbench.unregister(u'enaml.workbench.core')
