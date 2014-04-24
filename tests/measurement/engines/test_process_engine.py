# -*- coding: utf-8 -*-
from enaml.workbench.api import Workbench
import enaml
import os
import shutil
from time import sleep
from configobj import ConfigObj
from nose.tools import (assert_in, assert_not_in, assert_equal, assert_true,
                        assert_false)

from hqc_meas.measurement.measure import Measure
from hqc_meas.tasks.base_tasks import RootTask
from hqc_meas.tasks.tasks_util.test_tasks import SleepTask, PrintTask

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from enaml.workbench.ui.ui_manifest import UIManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from hqc_meas.utils.pref_manifest import PreferencesManifest
    from hqc_meas.log_system.log_manifest import LogManifest
    from hqc_meas.measurement.manifest import MeasureManifest
    from hqc_meas.task_management.manager_manifest import TaskManagerManifest
    from hqc_meas.instruments.manager_manifest import InstrManagerManifest
    from hqc_meas.measurement.engines.process_engine.process_engine_manifest\
        import ProcFilter
    from hqc_meas.measurement.engines.process_engine.process_engine\
        import ProcessEngine

    from ..helpers import TestSuiteManifest

from ...util import complete_line, process_app_events


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


class TestProcessEngine(object):

    test_dir = ''

    @classmethod
    def setup_class(cls):
        print complete_line(__name__ +
                            ':{}.setup_class()'.format(cls.__name__), '-', 77)
        # Creating dummy directory for prefs (avoid prefs interferences).
        directory = os.path.dirname(__file__)
        cls.test_dir = os.path.join(directory, '_temps')
        os.mkdir(cls.test_dir)

        # Creating dummy default.ini file in utils.
        util_path = os.path.join(directory, '..', '..', '..', 'hqc_meas',
                                 'utils')
        def_path = os.path.join(util_path, 'default.ini')
        if os.path.isfile(def_path):
            os.rename(def_path, os.path.join(util_path, '__default.ini'))

        # Making the preference manager look for info in test dir.
        default = ConfigObj(def_path)
        default['folder'] = cls.test_dir
        default['file'] = 'default_test.ini'
        default.write()

        conf = ConfigObj(os.path.join(cls.test_dir, 'default_test.ini'))
        path = 'hqc_meas.measurement.engines.process_engine'
        prefs = {'manifests': repr([(path, 'ProcessEngineManifest')])}
        conf[u'hqc_meas.measure'] = prefs
        conf.write()

    @classmethod
    def teardown_class(cls):
        print complete_line(__name__ +
                            ':{}.teardown_class()'.format(cls.__name__), '-',
                            77)
         # Removing pref files creating during tests.
        try:
            shutil.rmtree(cls.test_dir)

        # Hack for win32.
        except OSError:
            print 'OSError'
            dirs = os.listdir(cls.test_dir)
            for directory in dirs:
                shutil.rmtree(os.path.join(cls.test_dir), directory)
            shutil.rmtree(cls.test_dir)

        # Restoring default.ini file in utils
        directory = os.path.dirname(__file__)
        util_path = os.path.join(directory, '..', '..', '..', 'hqc_meas',
                                 'utils')
        def_path = os.path.join(util_path, 'default.ini')
        os.remove(def_path)

        aux = os.path.join(util_path, '__default.ini')
        if os.path.isfile(aux):
            os.rename(aux, def_path)

    def setup(self):

        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(UIManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(LogManifest())
        self.workbench.register(TaskManagerManifest())
        self.workbench.register(InstrManagerManifest())
        self.workbench.register(MeasureManifest())
        self.workbench.register(TestSuiteManifest())

    def teardown(self):
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        core.invoke_command(u'enaml.workbench.ui.close_workspace', {}, self)
        self.workbench.unregister(u'tests.suite')
        self.workbench.unregister(u'hqc_meas.measure')
        self.workbench.unregister(u'hqc_meas.task_manager')
        self.workbench.unregister(u'hqc_meas.instr_manager')
        self.workbench.unregister(u'hqc_meas.logging')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.ui')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_workspace_contribution(self):
        """ Test that the process does contribute to the workspace.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        plugin.selected_engine = u'hqc_meas.measure.engines.process_engine'

        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.measure.workspace'},
                            self)

        log_plugin = self.workbench.get_plugin(u'hqc_meas.logging')

        # Check the presence of the filters and handler in the log.
        assert_in(u'hqc_meas.measure.workspace.process_engine',
                  log_plugin.filter_ids)
        assert_in(u'hqc_meas.measure.engines.process_engine',
                  log_plugin.filter_ids)
        assert_in(u'hqc_meas.measure.engines.process_engine',
                  log_plugin.handler_ids)

        # Check the presence of the dock item.
        assert_true(plugin.workspace.dock_area.find('subprocess_log'))
        dock_item = plugin.workspace.dock_area.find('subprocess_log')
        assert_equal(dock_item.model.text, u'')

        # Unselected the engine.
        plugin.selected_engine = ''

        # Check the absence of the filters and handler in the log.
        assert_not_in(u'hqc_meas.measure.workspace.process_engine',
                      log_plugin.filter_ids)
        assert_not_in(u'hqc_meas.measure.engines.process_engine',
                      log_plugin.filter_ids)
        assert_not_in(u'hqc_meas.measure.engines.process_engine',
                      log_plugin.handler_ids)

        # Check the presence of the dock item.
        assert_false(plugin.workspace.dock_area.find('process_log'))

    def test_measure_processing1(self):
        """ Test the processing of a single measure (using the plugin).


        Test the communication with the plugin.

        """
        counter = 0
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure = self._create_measure(plugin)
        plugin.enqueued_measures.append(measure)

        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.measure.workspace'},
                            self)

        workspace = plugin.workspace
        plugin.selected_engine = u'hqc_meas.measure.engines.process_engine'
        workspace.start_processing_measures()

        # Check the engine state.
        engine = plugin.engine_instance
        assert_true(engine.active)
        while not engine._processing.is_set():
            sleep(0.01)

        while engine._processing.is_set():
            process_app_events()
            sleep(0.1)
            counter += 1
            if counter > 100:
                raise Exception('Task took too long to complete.')

        sleep(0.1)
        process_app_events()
        assert_equal(measure.status, 'COMPLETED')

        while engine.active:
            sleep(0.05)
            counter += 1
            if counter > 100:
                raise Exception('Engine took too long to exit.')

        # Check the engine exited properly.
        assert_false(engine._force_stop.is_set())

        # Check log.
        process_app_events()
        assert_not_in('test', workspace.log_model.text)
        assert_in('test',
                  workspace.dock_area.find('subprocess_log').model.text)

# For some tests don't need to use the plugin to start, stop the engine.

    def test_measure_processing2(self):
        """ Test the processing of a single measure (not using the plugin).


        Test the communication with the monitors (skip plugin tests) and with
        the log.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')

        measure = self._create_measure(plugin)
        monitor = measure.monitors.values()[0]

        engine = ProcessEngine(workbench=self.workbench)
        engine.observe('news', measure.monitors.values()[0].process_news)

        engine.prepare_to_run('test', measure.root_task,
                              measure.collect_entries_to_observe())

        monitor.start(None)

        # Check engine state.
        assert_true(engine._temp)
        assert_false(engine._meas_stop.is_set())
        assert_false(engine._stop.is_set())
        assert_false(engine._force_stop.is_set())
        assert_true(engine._process and engine._process.daemon)
        assert_true(engine._pipe)
        assert_true(engine._monitor_thread and engine._monitor_thread.daemon)
        assert_true(engine._log_thread and engine._log_thread.daemon)

        # Start the measure.
        engine.run()

        assert_true(engine.active)
        while not engine._processing.is_set():
            sleep(0.01)

        i = 0
        while i != 0 and engine._processing.is_set():
            sleep(0.2)
            i += 1
            if i > 50:
                raise Exception('Task took too long to complete.')

        engine.exit()

        while engine.active:
            sleep(0.1)
            i += 1
            if i > 100:
                raise Exception('Task took too long to complete.')

        # Check the monitor and log received the notifications.
        assert_in('root/print_message', monitor.engine_news)
        assert_equal(monitor.engine_news['root/print_message'], 'test')

    def test_measure_processing3(self):
        """ Test the processing of a measure failing the tests.

        Not terribly interesting just increase coverage but does not allow
        any true check.
        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')

        measure = self._create_measure(plugin)
        measure.root_task.default_path = ''

        engine = ProcessEngine(workbench=self.workbench)
        engine.prepare_to_run('test', measure.root_task,
                              measure.collect_entries_to_observe())

        # Check engine state.
        assert_true(engine._temp)
        assert_false(engine._meas_stop.is_set())
        assert_false(engine._stop.is_set())
        assert_false(engine._force_stop.is_set())
        assert_true(engine._process and engine._process.daemon)
        assert_true(engine._pipe)
        assert_true(engine._monitor_thread and engine._monitor_thread.daemon)
        assert_true(engine._log_thread and engine._log_thread.daemon)

        # Start the measure.
        engine.run()
        sleep(2)

        engine.exit()

    def test_stop_measure(self):
        """ Test stopping a measure but allowing to process next one.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure1 = self._create_measure(plugin)
        plugin.enqueued_measures.append(measure1)

        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.measure.workspace'},
                            self)

        workspace = plugin.workspace
        plugin.selected_engine = u'hqc_meas.measure.engines.process_engine'
        workspace.start_processing_measures()
        while not plugin.engine_instance._processing.is_set():
            sleep(0.01)

        # Stop the measure before it completes.
        workspace.stop_current_measure()

        while plugin.engine_instance._processing.is_set():
            sleep(0.01)
        process_app_events()

        # Check measures state.
        assert_equal(measure1.status, 'INTERRUPTED')

    def test_stop_processing(self):
        """ Test stopping the whole processing loop.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure1 = self._create_measure(plugin)
        plugin.enqueued_measures.append(measure1)

        measure2 = self._create_measure(plugin)
        plugin.enqueued_measures.append(measure2)

        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.measure.workspace'},
                            self)

        workspace = plugin.workspace
        plugin.selected_engine = u'hqc_meas.measure.engines.process_engine'
        workspace.start_processing_measures()
        while not plugin.engine_instance._processing.is_set():
            sleep(0.01)

        # Stop the measure before it completes.
        workspace.stop_processing_measures()

        while plugin.engine_instance._processing.is_set():
            sleep(0.01)
        process_app_events()

        # Check measures state.
        assert_equal(measure1.status, 'INTERRUPTED')

        assert_equal(measure2.status, 'READY')

    def test_exit_measure(self):
        """ Test stopping a measure (force) but allowing to process next one.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure1 = self._create_measure(plugin)
        plugin.enqueued_measures.append(measure1)

        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.measure.workspace'},
                            self)

        workspace = plugin.workspace
        plugin.selected_engine = u'hqc_meas.measure.engines.process_engine'
        workspace.start_processing_measures()
        while not plugin.engine_instance._processing.is_set():
            sleep(0.01)

        # Force stop the measure before it completes.
        workspace.force_stop_measure()

        while plugin.engine_instance._processing.is_set():
            sleep(0.01)
        process_app_events()

        # Check measures state.
        assert_equal(measure1.status, 'INTERRUPTED')

    def test_exit_processing(self):
        """ Test stopping the whole processing loop (force).

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure1 = self._create_measure(plugin)
        plugin.enqueued_measures.append(measure1)

        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.measure.workspace'},
                            self)

        workspace = plugin.workspace
        plugin.selected_engine = u'hqc_meas.measure.engines.process_engine'
        workspace.start_processing_measures()
        while not plugin.engine_instance._processing.is_set():
            sleep(0.01)

        # Force stop the processing.
        workspace.force_stop_processing()

        while plugin.engine_instance._processing.is_set():
            sleep(0.01)
        process_app_events()

        # Check measures state.
        assert_equal(measure1.status, 'INTERRUPTED')

    def _create_measure(self, plugin):
        """ Create a measure.

        """
        measure = Measure(plugin=plugin, name='Test1')
        measure.root_task = RootTask(default_path=self.test_dir)
        children = [SleepTask(task_name='sleep1', time=0.5),
                    PrintTask(task_name='print', message='test'),
                    SleepTask(task_name='sleep2', time=0.1)]
        measure.root_task.children_task.extend(children)
        measure.status = 'READY'
        monitor_decl = plugin.monitors[u'monitor1']
        measure.add_monitor(monitor_decl.id,
                            monitor_decl.factory(monitor_decl,
                                                 self.workbench))
        return measure


class Record(object):
    """ False record object.

    """
    def __init__(self, process_name):
        self.processName = process_name


def test_proc_filter1():
    filt = ProcFilter(reject_if_equal=False)
    rec = Record('Test')
    assert_false(filt.filter(rec))


def test_proc_filter2():
    filt = ProcFilter(reject_if_equal=False)
    rec = Record('MeasureProcess')
    assert_true(filt.filter(rec))


def test_proc_filter3():
    filt = ProcFilter(reject_if_equal=True)
    rec = Record('Test')
    assert_true(filt.filter(rec))


def test_proc_filter4():
    filt = ProcFilter(reject_if_equal=True)
    rec = Record('MeasureProcess')
    assert_false(filt.filter(rec))
