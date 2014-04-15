from enaml.workbench.api import Workbench
import enaml
import os
import shutil
from configobj import ConfigObj
from nose.tools import (assert_in, assert_not_in, assert_equal, assert_true,
                        assert_false)

from hqc_meas.measurement.measure import Measure
from hqc_meas.measurement.workspace import LOG_ID
from hqc_meas.tasks.base_tasks import RootTask

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from enaml.workbench.ui.ui_manifest import UIManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from hqc_meas.utils.pref_manifest import PreferencesManifest
    from hqc_meas.log_system.log_manifest import LogManifest
    from hqc_meas.measurement.manifest import MeasureManifest
    from hqc_meas.task_management.manager_manifest import TaskManagerManifest
    from hqc_meas.instruments.manager_manifest import InstrManagerManifest

    from .helpers import TestSuiteManifest

from ..util import complete_line


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

    def test_life_cycle(self):
        """ Test that workspace starting/closing goes well

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.measure.workspace'},
                            self)

        plugin = self.workbench.get_plugin(u'hqc_meas.measure')
        log_plugin = self.workbench.get_plugin(u'hqc_meas.logging')

        # Check the plugin got the workspace
        assert_true(plugin.workspace)
        workspace = plugin.workspace

        # Check the workspace registration.
        assert_true(workspace.log_model)
        assert_in(LOG_ID, log_plugin.handler_ids)

        # Check a blank measure was created.
        assert_true(plugin.edited_measure)

        # TODO check engine contribution

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
