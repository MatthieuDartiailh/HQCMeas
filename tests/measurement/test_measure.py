# -*- coding: utf-8 -*-
# =============================================================================
# module : measurement/test_measure.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from enaml.workbench.api import Workbench
import enaml
import os
from configobj import ConfigObj
from nose.tools import (assert_in, assert_not_in, assert_equal, assert_true,
                        assert_false)

from hqc_meas.tasks.api import RootTask
from hqc_meas.measurement.measure import Measure
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state.manifest import StateManifest
    from hqc_meas.utils.preferences.manifest import PreferencesManifest
    from hqc_meas.utils.dependencies.manifest import DependenciesManifest
    from hqc_meas.measurement.manifest import MeasureManifest
    from hqc_meas.tasks.manager.manifest import TaskManagerManifest

    from .helpers import TestSuiteManifest, Checker

from ..util import complete_line, remove_tree, create_test_dir


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


class TestPluginCoreFunctionalities(object):

    test_dir = ''

    @classmethod
    def setup_class(cls):
        print complete_line(__name__ +
                            ':{}.setup_class()'.format(cls.__name__), '-', 77)
        # Creating dummy directory for prefs (avoid prefs interferences).
        directory = os.path.dirname(__file__)
        cls.test_dir = os.path.join(directory, '_temps')
        create_test_dir(cls.test_dir)

        # Creating dummy default.ini file in utils.
        util_path = os.path.join(directory, '..', '..', 'hqc_meas', 'utils',
                                 'preferences')
        def_path = os.path.join(util_path, 'default.ini')

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
        remove_tree(cls.test_dir)

        # Restoring default.ini file in utils
        directory = os.path.dirname(__file__)
        util_path = os.path.join(directory, '..', '..', 'hqc_meas', 'utils',
                                 'preferences')
        def_path = os.path.join(util_path, 'default.ini')
        os.remove(def_path)

    def setup(self):

        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(DependenciesManifest())
        self.workbench.register(TaskManagerManifest())
        self.workbench.register(MeasureManifest())
        self.workbench.register(TestSuiteManifest())

    def teardown(self):
        try:
            self.workbench.unregister(u'tests.suite')
        except ValueError:
            pass
        self.workbench.unregister(u'hqc_meas.measure')
        self.workbench.unregister(u'hqc_meas.task_manager')
        self.workbench.unregister(u'hqc_meas.dependencies')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_save_load_measure1(self):
        """ Test saving a measure to a file and reloading it.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure = Measure(plugin=plugin, name='Test', status='Under test')
        measure.root_task = RootTask(default_path=self.test_dir)

        # Needed because of Atom returning a _DictProxy
        measure.checks = dict(plugin.checks)
        # Needed because of Atom returning a _DictProxy
        measure.headers = dict(plugin.headers)
        # Adding a monitor.
        monitor_decl = plugin.monitors[u'monitor1']
        measure.add_monitor(monitor_decl.id,
                            monitor_decl.factory(monitor_decl,
                                                 self.workbench))
        measure.monitors[u'monitor1'].save_test = True

        path = os.path.join(self.test_dir, 'saved_measure.ini')
        # Save measure.
        measure.save_measure(path)

        assert_true(os.path.isfile(path))

        # Load measure.
        loaded = Measure.load_measure(plugin, path)

        assert_equal(loaded.name, 'Test')
        assert_equal(loaded.root_task.default_path, self.test_dir)
        assert_equal(loaded.checks, dict(plugin.checks))
        assert_equal(loaded.headers, dict(plugin.headers))
        assert_in(u'monitor1', loaded.monitors)

        monitor = loaded.monitors[u'monitor1']
        assert_true(monitor.save_test)

        # Check that all values have been correctly updated.
        monitor = measure.monitors[u'monitor1']
        assert_equal(monitor.measure_name, measure.root_task.meas_name)
        assert_equal(monitor.measure_status, measure.status)
        assert_equal(monitor.updated, {'root/default_path': 1})
        assert_equal(measure.collect_entries_to_observe(),
                     ['root/default_path'])

        # Check that the notifier is correctly observed.
        assert_true(measure.root_task.task_database.has_observers('notifier'))

    def test_save_load_measure2(self):
        """ Test saving a measure to a file and reloading it with absent tools.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure = Measure(plugin=plugin, name='Test', status='Under test')
        measure.root_task = RootTask(default_path=self.test_dir)

        # Needed because of Atom returning a _DictProxy
        measure.checks = dict(plugin.checks)
        # Needed because of Atom returning a _DictProxy
        measure.headers = dict(plugin.headers)
        # Adding a monitor.
        monitor_decl = plugin.monitors[u'monitor1']
        measure.add_monitor(monitor_decl.id,
                            monitor_decl.factory(monitor_decl,
                                                 self.workbench))
        measure.monitors[u'monitor1'].save_test = True

        path = os.path.join(self.test_dir, 'saved_measure.ini')
        # Save measure.
        measure.save_measure(path)

        assert_true(os.path.isfile(path))

        # Remove test_suite
        self.workbench.unregister(u'tests.suite')

        # Load measure.
        loaded = Measure.load_measure(plugin, path)

        assert_equal(loaded.name, 'Test')
        assert_equal(loaded.root_task.default_path, self.test_dir)
        assert_equal(loaded.checks, {})
        assert_equal(loaded.headers, {})
        assert_equal(loaded.monitors, {})

        self.workbench.register(TestSuiteManifest())

    def test_override_saved_measure(self):
        """ Test that overriding a measure does override evrything.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure = Measure(plugin=plugin, name='Test', status='Under test')
        measure.root_task = RootTask(default_path=self.test_dir)

        # Needed because of Atom returning a _DictProxy
        measure.checks = dict(plugin.checks)
        # Needed because of Atom returning a _DictProxy
        measure.headers = dict(plugin.headers)
        # Adding a monitor.
        monitor_decl = plugin.monitors[u'monitor1']
        measure.add_monitor(monitor_decl.id,
                            monitor_decl.factory(monitor_decl,
                                                 self.workbench))
        measure.monitors[u'monitor1'].save_test = True

        path = os.path.join(self.test_dir, 'saved_measure.ini')
        # Save measure.
        measure.save_measure(path)

        # Create a new measure without headers and checks and test that the old
        # values are not in the config file.
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure = Measure(plugin=plugin, name='Test', status='Under test')
        measure.root_task = RootTask(default_path=self.test_dir)

        measure.save_measure(path)

        conf = ConfigObj(path)
        assert_equal(conf['checks'], '[]')
        assert_equal(conf['headers'], '[]')

    def test_run_checks1(self):
        """ Test running checks for a measure. Passing.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure = Measure(plugin=plugin)
        measure.root_task = RootTask(default_path=self.test_dir)

        # Needed because of Atom returning a _DictProxy
        measure.checks = dict(plugin.checks)

        Checker.test_pass = True
        res, errors = measure.run_checks(self.workbench)

        assert_true(res)
        assert_equal(errors, {})

    def test_run_checks2(self):
        """ Test running checks for a measure. Failing because added check.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure = Measure(plugin=plugin)
        measure.root_task = RootTask(default_path=self.test_dir)

        # Needed because of Atom returning a _DictProxy
        measure.checks = dict(plugin.checks)

        Checker.test_pass = False
        res, errors = measure.run_checks(self.workbench)

        assert_false(res)
        assert_equal(errors, {u'check1': {'test': 'Failed'}})

    def test_run_checks3(self):
        """ Test running checks for a measure. Failing because of RootTask.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure = Measure(plugin=plugin)
        measure.root_task = RootTask()

        # Needed because of Atom returning a _DictProxy
        measure.checks = dict(plugin.checks)

        Checker.test_pass = True
        res, errors = measure.run_checks(self.workbench)

        assert_false(res)
        assert_in(u'internal', errors)
        assert_not_in(u'check1', errors)

    def test_run_checks4(self):
        """ Test running checks for a measure. Passing without added.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure = Measure(plugin=plugin)
        measure.root_task = RootTask()
        measure.root_task = RootTask(default_path=self.test_dir)

        # Needed because of Atom returning a _DictProxy
        measure.checks = dict(plugin.checks)

        Checker.test_pass = False
        res, errors = measure.run_checks(self.workbench, internal_only=True)

        assert_true(res)
        assert_equal(errors, {})

    def test_collect_headers(self):
        """ Test header collection.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure = Measure(plugin=plugin)
        measure.root_task = RootTask()

        # Needed because of Atom returning a _DictProxy
        measure.headers = dict(plugin.headers)
        measure.collect_headers(self.workbench)

        assert_equal(measure.root_task.default_header,
                     'Test header\nTest header')

    def test_add_monitor1(self):
        """ Test adding a new monitor.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure = Measure(plugin=plugin, name='Test', status='Under test')
        measure.root_task = RootTask()

        # Be sure that there is no observers for the database
        assert_false(measure.root_task.task_database.has_observers('notifier'))

        monitor_decl = plugin.monitors[u'monitor1']
        measure.add_monitor(monitor_decl.id,
                            monitor_decl.factory(monitor_decl,
                                                 self.workbench))

        # Check the monitor is now in the list of the measure monitors
        assert_in(u'monitor1', measure.monitors)

        # Check that all values have been correctly updated.
        monitor = measure.monitors[u'monitor1']
        assert_equal(monitor.measure_name, measure.root_task.meas_name)
        assert_equal(monitor.measure_status, measure.status)
        assert_equal(monitor.updated, {'root/default_path': 1})
        assert_equal(measure.collect_entries_to_observe(),
                     ['root/default_path'])

        # Check that the notifier is correctly observed.
        assert_true(measure.root_task.task_database.has_observers('notifier'))

    def test_add_monitor2(self):
        """ Test adding twice the same monitor second time should be a no-op.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure = Measure(plugin=plugin, name='Test', status='Under test')
        measure.root_task = RootTask()

        # Be sure that there is no observers for the database
        assert_false(measure.root_task.task_database.has_observers('notifier'))

        monitor_decl = plugin.monitors[u'monitor1']
        measure.add_monitor(monitor_decl.id,
                            monitor_decl.factory(monitor_decl,
                                                 self.workbench))

        measure.add_monitor(monitor_decl.id,
                            monitor_decl.factory(monitor_decl,
                                                 self.workbench))

    def test_remove_monitor1(self):
        """ Test removing a monitor.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure = Measure(plugin=plugin, name='Test', status='Under test')
        measure.root_task = RootTask()

        test_obs = lambda change: False
        measure.root_task.task_database.observe('notifier', test_obs)

        monitor_decl = plugin.monitors[u'monitor1']
        measure.add_monitor(monitor_decl.id,
                            monitor_decl.factory(monitor_decl,
                                                 self.workbench))
        measure.remove_monitor(u'monitor1')

        assert_not_in(u'monitor1', measure.monitors)

        # Check that the notifier is not observed anymore but that other
        # observers are not deleted.
        assert_true(measure.root_task.task_database.has_observers('notifier'))
        measure.root_task.task_database.unobserve('notifier', test_obs)
        assert_false(measure.root_task.task_database.has_observers('notifier'))

    def test_remove_monitor2(self):
        """ Test removing a non-existent monitor (should be a no-op).

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure = Measure(plugin=plugin, name='Test', status='Under test')
        measure.root_task = RootTask()

        measure.remove_monitor(u'monitor1')

    def test_setting_state(self):
        """ Test entering the edition state for a measure.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure = Measure(plugin=plugin, name='Test', status='Under test')
        measure.root_task = RootTask()

        # Be sure that there is no observers for the database
        assert_false(measure.root_task.task_database.has_observers('notifier'))

        monitor_decl = plugin.monitors[u'monitor1']
        measure.add_monitor(monitor_decl.id,
                            monitor_decl.factory(monitor_decl,
                                                 self.workbench))

        assert_true(measure.root_task.task_database.has_observers('notifier'))

        measure.enter_running_state()

        assert_false(measure.root_task.task_database.has_observers('notifier'))

        measure.enter_edition_state()

        assert_true(measure.root_task.task_database.has_observers('notifier'))

    def test_observer_root_task(self):
        """ Test the behavior of the root_task observer.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure = Measure(plugin=plugin, name='Test', status='Under test')
        root_task1 = RootTask()
        root_task2 = RootTask()

        measure.root_task = root_task1

        monitor_decl = plugin.monitors[u'monitor1']
        measure.add_monitor(monitor_decl.id,
                            monitor_decl.factory(monitor_decl,
                                                 self.workbench))

        measure.root_task = root_task2

        assert_equal(measure.monitors[u'monitor1'].updated,
                     {'root/default_path': 1})
        assert_equal(measure.collect_entries_to_observe(),
                     ['root/default_path'])
        assert_false(root_task1.task_database.has_observers('notifier'))
        assert_true(root_task2.task_database.has_observers('notifier'))

    def test_observer_name(self):
        """ Test observer for measure name.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure = Measure(plugin=plugin, name='Test', status='Under test')
        measure.root_task = RootTask()

        monitor_decl = plugin.monitors[u'monitor1']
        measure.add_monitor(monitor_decl.id,
                            monitor_decl.factory(monitor_decl,
                                                 self.workbench))

        measure.root_task.meas_name = 'Test2'

        assert_equal(measure.monitors[u'monitor1'].measure_name, 'Test2')

    def test_observer_status(self):
        """ Test observer for measure status.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        measure = Measure(plugin=plugin, name='Test', status='Under test')
        measure.root_task = RootTask()

        monitor_decl = plugin.monitors[u'monitor1']
        measure.add_monitor(monitor_decl.id,
                            monitor_decl.factory(monitor_decl,
                                                 self.workbench))

        measure.status = 'Test over'

        assert_equal(measure.monitors[u'monitor1'].measure_status, 'Test over')
