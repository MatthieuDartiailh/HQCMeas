# -*- coding: utf-8 -*-
#==============================================================================
# module : test_workspace.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from enaml.workbench.api import Workbench
import enaml
import os
import shutil
import logging
from configobj import ConfigObj
from nose.tools import (assert_in, assert_not_in, assert_equal, assert_true,
                        assert_false, assert_is, assert_is_not)

from hqc_meas.measurement.measure import Measure
from hqc_meas.measurement.workspace import LOG_ID
from hqc_meas.tasks.base_tasks import RootTask

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from enaml.workbench.ui.ui_manifest import UIManifest
    from hqc_meas.app_manifest import HqcAppManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from hqc_meas.utils.pref_manifest import PreferencesManifest
    from hqc_meas.log_system.log_manifest import LogManifest
    from hqc_meas.measurement.manifest import MeasureManifest
    from hqc_meas.task_management.manager_manifest import TaskManagerManifest
    from hqc_meas.instruments.manager_manifest import InstrManagerManifest

    from .helpers import TestSuiteManifest

from ..util import complete_line, process_app_events, close_all_windows


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
        # Creating dummy directory for prefs (avoid prefs interferences).
        directory = os.path.dirname(__file__)
        cls.test_dir = os.path.join(directory, '_temps')
        os.mkdir(cls.test_dir)

        # Creating dummy default.ini file in utils.
        util_path = os.path.join(directory, '..', '..', 'hqc_meas', 'utils')
        def_path = os.path.join(util_path, 'default.ini')
        if os.path.isfile(def_path):
            os.rename(def_path, os.path.join(util_path, '__default.ini'))

        # Making the preference manager look for info in test dir.
        default = ConfigObj(def_path)
        default['folder'] = cls.test_dir
        default['file'] = 'default_test.ini'
        default.write()

        conf = ConfigObj(os.path.join(cls.test_dir, 'default_test.ini'))
        conf[u'hqc_meas.measure'] = {}
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
        util_path = os.path.join(directory, '..', '..', 'hqc_meas', 'utils')
        def_path = os.path.join(util_path, 'default.ini')
        os.remove(def_path)

        aux = os.path.join(util_path, '__default.ini')
        if os.path.isfile(aux):
            os.rename(aux, def_path)

    def setup(self):

        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(UIManifest())
        self.workbench.register(HqcAppManifest())
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
        self.workbench.unregister(u'hqc_meas.app')
        self.workbench.unregister(u'enaml.workbench.ui')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_life_cycle(self):
        """ Test that workspace starting/closing goes well

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        plugin.selected_engine = u'engine1'

        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.measure.workspace'},
                            self)

        log_plugin = self.workbench.get_plugin(u'hqc_meas.logging')

        # Check the plugin got the workspace
        assert_true(plugin.workspace)
        workspace = plugin.workspace

        # Check the workspace registration.
        assert_true(workspace.log_model)
        assert_in(LOG_ID, log_plugin.handler_ids)

        logger = logging.getLogger(__name__)
        logger.info('test')
        process_app_events()
        assert_in('test', workspace.log_model.text)

        # Check a blank measure was created.
        assert_true(plugin.edited_measure)
        assert_true(plugin.edited_measure.plugin)

        # Check the engine engine is contributing.
        assert_true(plugin.engines[u'engine1'].contributing)

        # Check the workspace is observing the selected_engine
        observer = workspace._update_engine_contribution
        assert_true(plugin.has_observer('selected_engine', observer))

        cmd = u'enaml.workbench.ui.close_workspace'
        core.invoke_command(cmd, {}, self)

        # Check the workspace is not observing anymore the selected_engine
        assert_false(plugin.has_observer('selected_engine', observer))

        # Check the workspace removed its log handler.
        assert_not_in(LOG_ID, log_plugin.handler_ids)

        # Check the reference to the workspace was destroyed.
        assert_equal(plugin.workspace, None)

        # Check the engine contribution was removed.
        assert_false(plugin.engines[u'engine1'].contributing)

    def test_engine_contribution_observer(self):
        """ Test the contribution of the selected engine is correctly handled.

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.measure.workspace'},
                            self)

        plugin = self.workbench.get_plugin(u'hqc_meas.measure')

        plugin.selected_engine = u'engine1'
        assert_true(plugin.engines[u'engine1'].contributing)

        plugin.selected_engine = u''
        assert_false(plugin.engines[u'engine1'].contributing)

    def test_enqueue_measure1(self):
        """ Test enqueueing a measure passing the tests.

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.measure.workspace'},
                            self)

        plugin = self.workbench.get_plugin(u'hqc_meas.measure')

        measure = Measure(plugin=plugin, name='Test')
        measure.root_task = RootTask(default_path=self.test_dir)
        plugin.edited_measure = measure

        res = plugin.workspace.enqueue_measure(plugin.edited_measure)

        assert_true(res)
        assert_false(measure.root_task.run_time)
        assert_true(plugin.enqueued_measures)
        en_meas = plugin.enqueued_measures[0]
        assert_is_not(en_meas, measure)
        assert_equal(en_meas.status, 'READY')
        assert_equal(en_meas.infos,
                     'The measure is ready to be performed by an engine.')
        assert_in('drivers', en_meas.root_task.run_time)
        assert_in('profiles', en_meas.store)

    def test_enqueue_measure2(self):
        """ Test enqueueing a measure failing the tests.

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.measure.workspace'},
                            self)

        plugin = self.workbench.get_plugin(u'hqc_meas.measure')

        measure = Measure(plugin=plugin, name='Test')
        measure.root_task = RootTask()
        plugin.edited_measure = measure

        res = plugin.workspace.enqueue_measure(plugin.edited_measure)

        assert_false(res)
        assert_false(measure.root_task.run_time)
        assert_false(plugin.enqueued_measures)

        close_all_windows()

    def test_reenqueue_measure(self):
        """ Test re-enqueueing a measure.

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.measure.workspace'},
                            self)

        plugin = self.workbench.get_plugin(u'hqc_meas.measure')

        measure = self._create_measure(plugin)
        measure.enter_running_state()

        plugin.workspace.reenqueue_measure(measure)

        assert_equal(measure.status, 'READY')
        assert_equal(measure.infos,
                     'Measure re-enqueued by the user')
        assert_true(measure.root_task.task_database.has_observers('notifier'))

    def test_plugin_find_next_measure1(self):
        """ Test plugin.find_next_measure, first measure is ok.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure = Measure(plugin=plugin, name='Test')
        measure.root_task = RootTask()
        plugin.enqueued_measures.append(measure)

        meas = plugin.find_next_measure()
        assert_is(measure, meas)

    def test_plugin_find_next_measure2(self):
        """ Test plugin.find_next_measure when measures should be skipped.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure1 = Measure(plugin=plugin, name='Test1')
        measure1.root_task = RootTask()
        measure1.status = 'SKIPPED'
        plugin.enqueued_measures.append(measure1)

        measure2 = Measure(plugin=plugin, name='Test2')
        measure2.root_task = RootTask()
        measure2.status = 'EDITING'
        plugin.enqueued_measures.append(measure2)

        measure3 = Measure(plugin=plugin, name='Test3')
        measure3.root_task = RootTask()
        measure3.status = 'READY'
        plugin.enqueued_measures.append(measure3)

        meas = plugin.find_next_measure()
        assert_is(measure3, meas)

    def test_plugin_find_next_measure3(self):
        """ Test plugin.find_next_measure when no measures can be sent.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure1 = Measure(plugin=plugin, name='Test1')
        measure1.root_task = RootTask()
        measure1.status = 'SKIPPED'
        plugin.enqueued_measures.append(measure1)

        measure2 = Measure(plugin=plugin, name='Test2')
        measure2.root_task = RootTask()
        measure2.status = 'EDITING'
        plugin.enqueued_measures.append(measure2)

        meas = plugin.find_next_measure()
        assert_is(None, meas)

    def test_measure_processing1(self):
        """ Test the processing of a single measure.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure1 = self._create_measure(plugin)
        plugin.enqueued_measures.append(measure1)

        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.measure.workspace'},
                            self)

        workspace = plugin.workspace
        plugin.selected_engine = u'engine1'
        workspace.start_processing_measures()

        # Check the right flag is set in the plugin.
        assert_in('processing', plugin.flags)

        # Check an engine instance was created and is processing the measure.
        assert_true(plugin.engine_instance)
        engine = plugin.engine_instance
        assert_true(engine.ready)
        assert_true(engine.running)
        # Check the plugin observe the done event.
        assert_true(engine.has_observer('done', plugin._listen_to_engine))

        # Check the measure has been registered as running and its status been
        # updated.
        assert_true(plugin.running_measure)
        measure = plugin.running_measure
        assert_equal(measure.status, 'RUNNING')
        assert_equal(measure.infos, 'The measure is running')

        # Check the monitors connections, that it started and received notif.
        monitor = measure.monitors.values()[0]
        assert_true(engine.has_observer('news', monitor.process_news))
        assert_equal(monitor.black_box, ['Started'])
        assert_equal(monitor.engine_news, {'root/default_path': 'test'})

        # Make the engine send the done event.
        engine.complete_measure()

        # Check engine state.
        assert_false(engine.active)
        assert_false(engine.has_observers('news'))

        # Check measure state.
        assert_equal(measure.status, 'COMPLETED')
        assert_equal(measure.infos, 'Measure successfully completed')

        # Check plugin state.
        assert_false(plugin.flags)

        # Closing workspace.
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        core.invoke_command(u'enaml.workbench.ui.close_workspace', {}, self)

        # Check monitors stopped properly.
        assert_equal(monitor.black_box, ['Started', 'Stopped'])

    def test_measure_processing2(self):
        """ Test the processing of a two measures in a row.

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
        plugin.selected_engine = u'engine1'
        workspace.start_processing_measures()

        # Check the right flag is set in the plugin.
        assert_in('processing', plugin.flags)

         # Check an engine instance was created and is processing the measure.
        assert_true(plugin.engine_instance)
        engine = plugin.engine_instance

        # Check the measure has been registered as running and its status been
        # updated.
        assert_true(plugin.running_measure)
        measure = plugin.running_measure
        assert_is(measure, measure1)

        # Make the engine send the done event.
        engine.complete_measure()

        # Check measure1 state.
        assert_equal(measure1.status, 'COMPLETED')
        assert_equal(measure1.infos, 'Measure successfully completed')

         # Check the measure has been registered as running and its status been
        # updated.
        assert_true(plugin.running_measure)
        measure = plugin.running_measure
        assert_is(measure, measure2)

        # Make the engine send the done event.
        engine.complete_measure()

        # Check engine state.
        assert_false(engine.active)
        assert_false(engine.has_observers('news'))

        # Check measure state.
        assert_equal(measure2.status, 'COMPLETED')
        assert_equal(measure2.infos, 'Measure successfully completed')

        assert_false(plugin.flags)

    def test_measure_processing3(self):
        """ Test the processing of a measure failing the tests.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure1 = self._create_measure(plugin)
        measure1.root_task.default_path = ''
        plugin.enqueued_measures.append(measure1)

        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.measure.workspace'},
                            self)

        workspace = plugin.workspace
        plugin.selected_engine = u'engine1'
        workspace.start_processing_measures()

        process_app_events()

        # Check the right flag is set in the plugin.
        assert_not_in('processing', plugin.flags)

        # Check the measure status has been updated.
        assert_true(plugin.running_measure)
        measure = plugin.running_measure
        assert_equal(measure.status, 'FAILED')
        assert_equal(measure.infos, 'Failed to pass the built in tests')

        assert_false(plugin.flags)

    def test_measure_processing4(self):
        """ Test the processing of a measure failing to get some profiles.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure1 = self._create_measure(plugin)
        plugin.enqueued_measures.append(measure1)

        measure1.store['profiles'] = ['Test']

        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.measure.workspace'},
                            self)

        workspace = plugin.workspace
        plugin.selected_engine = u'engine1'
        workspace.start_processing_measures()

        process_app_events()

        # Check the right flag is set in the plugin.
        assert_not_in('processing', plugin.flags)

        # Check the measure status has been updated.
        assert_true(plugin.running_measure)
        measure = plugin.running_measure
        assert_equal(measure.status, 'SKIPPED')
        assert_equal(measure.infos, 'Failed to get requested profiles')

        assert_false(plugin.flags)

    def test_processing_single_measure(self):
        """ Test processing only a specific measure.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure1 = self._create_measure(plugin)
        plugin.enqueued_measures.append(measure1)

        measure2 = self._create_measure(plugin)
        plugin.enqueued_measures.append(measure2)

        measure3 = self._create_measure(plugin)
        plugin.enqueued_measures.append(measure3)

        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.measure.workspace'},
                            self)

        workspace = plugin.workspace
        plugin.selected_engine = u'engine1'
        workspace.process_single_measure(measure2)

        # Check the right flag is set in the plugin.
        assert_in('processing', plugin.flags)
        assert_in('stop_processing', plugin.flags)

        # Check the measure has been registered as running and its status been
        # updated.
        assert_true(plugin.running_measure)
        measure = plugin.running_measure
        assert_equal(measure.status, 'RUNNING')
        assert_equal(measure.infos, 'The measure is running')
        assert_is(measure, measure2)

        # Make the engine send the done event.
        plugin.engine_instance.complete_measure()

        # Check measures state.
        assert_equal(measure1.status, 'READY')

        assert_equal(measure2.status, 'COMPLETED')

        assert_equal(measure3.status, 'READY')

        # Check plugin state.
        assert_false(plugin.flags)

        assert_false(plugin.engine_instance.running)

    def test_stop_measure(self):
        """ Test stopping a measure but allowing to process next one.

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
        plugin.selected_engine = u'engine1'
        workspace.start_processing_measures()

        # Stop the measure before it completes.
        workspace.stop_current_measure()

        # Complete the second measure.
        plugin.engine_instance.complete_measure()

        # Check measures state.
        assert_equal(measure1.status, 'INTERRUPTED')

        assert_equal(measure2.status, 'COMPLETED')

        # Check plugin state.
        assert_false(plugin.flags)
        assert_false(plugin.engine_instance.running)

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
        plugin.selected_engine = u'engine1'
        workspace.start_processing_measures()

        # Stop the measure before it completes.
        workspace.stop_processing_measures()

        # Check measures state.
        assert_equal(measure1.status, 'INTERRUPTED')

        assert_equal(measure2.status, 'READY')

        # Check plugin state.
        assert_false(plugin.flags)
        assert_false(plugin.engine_instance.running)

    def test_exit_measure(self):
        """ Test stopping a measure (force) but allowing to process next one.

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
        plugin.selected_engine = u'engine1'
        workspace.start_processing_measures()

        plugin.engine_instance.allow_stop = False
        workspace.stop_current_measure()

        # Check the plugin flags.
        assert_in('stop_attempt', plugin.flags)

        # Force stop the measure before it completes.
        workspace.force_stop_measure()

        # Complete the second measure.
        plugin.engine_instance.allow_stop = True
        plugin.engine_instance.complete_measure()

        # Check measures state.
        assert_equal(measure1.status, 'INTERRUPTED')

        assert_equal(measure2.status, 'COMPLETED')

        # Check plugin state.
        assert_false(plugin.flags)
        assert_false(plugin.engine_instance.running)

    def test_exit_processing(self):
        """ Test stopping the whole processing loop (force).

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
        plugin.selected_engine = u'engine1'
        workspace.start_processing_measures()

        plugin.engine_instance.allow_stop = False
        workspace.stop_current_measure()

        # Check the plugin flags.
        assert_in('stop_attempt', plugin.flags)

        # Force stop the processing.
        workspace.force_stop_processing()

        # Check measures state.
        assert_equal(measure1.status, 'INTERRUPTED')

        assert_equal(measure2.status, 'READY')

        # Check plugin state.
        assert_false(plugin.flags)
        assert_false(plugin.engine_instance.running)

    def _create_measure(self, plugin):
        """ Create a measure.

        """
        measure = Measure(plugin=plugin, name='Test1')
        measure.root_task = RootTask(default_path=self.test_dir)
        measure.status = 'READY'
        monitor_decl = plugin.monitors[u'monitor1']
        measure.add_monitor(monitor_decl.id,
                            monitor_decl.factory(monitor_decl,
                                                 self.workbench))
        return measure
