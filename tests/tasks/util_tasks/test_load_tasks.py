# -*- coding: utf-8 -*-
# =============================================================================
# module : hqc_meas/tasks/tasks_util/test_load_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from nose.tools import (assert_equal, assert_true, assert_false, assert_in,
                        assert_is, assert_is_instance)
from nose.plugins.attrib import attr
from multiprocessing import Event
from enaml.workbench.api import Workbench
import numpy as np
import os

from hqc_meas.tasks.api import RootTask
from hqc_meas.tasks.tasks_util.load_tasks import (LoadArrayTask,
                                                  CSVLoadInterface)

import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state.manifest import StateManifest
    from hqc_meas.utils.preferences.manifest import PreferencesManifest
    from hqc_meas.tasks.manager.manifest import TaskManagerManifest

    from hqc_meas.tasks.tasks_util.views.load_views\
        import LoadArrayView

from ...util import process_app_events, close_all_windows


FOLDER_PATH = os.path.dirname(__file__)


class TestLoadArrayTaskCSVInterface(object):

    @classmethod
    def setup_class(cls):
        cls.data = np.zeros((5,), dtype=[('Freq', 'f8'), ('Log', 'f8')])
        full_path = os.path.join(FOLDER_PATH, 'fake.dat')
        with open(full_path, 'wb') as f:

            f.write('# this is a comment \n')
            f.write('\t'.join(cls.data.dtype.names) + '\n')

            np.savetxt(f, cls.data, delimiter='\t')

    @classmethod
    def teardown_class(cls):
        full_path = os.path.join(FOLDER_PATH, 'fake.dat')
        if os.path.isfile(full_path):
            os.remove(full_path)

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = LoadArrayTask(task_name='Test')
        self.task.interface = CSVLoadInterface()
        self.task.folder = FOLDER_PATH
        self.task.filename = 'fake.dat'
        self.root.children_task.append(self.task)

    def test_check1(self):
        # Test everything is ok if folder and filename are correct.
        test, traceback = self.task.check()
        assert_true(test)
        assert_false(traceback)
        array = self.task.get_from_database('Test_array')
        assert_equal(array.dtype.names, ('Freq', 'Log'))

    def test_check2(self):
        # Test handling wrong folder and filename.
        self.task.folder = '{rr}'
        self.task.filename = '{tt}'
        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 2)

    def test_check3(self):
        # Test handling an absent file.
        self.task.filename = 'tt'
        test, traceback = self.task.check()
        assert_true(test)
        assert_equal(len(traceback), 1)

    def test_perform1(self):
        # Test loading a csv file.
        self.task.perform()
        array = self.task.get_from_database('Test_array')
        np.testing.assert_array_equal(array, self.data)


@attr('ui')
class TestLoadArrayView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = LoadArrayTask(task_name='Test')
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
        core = self.workbench.get_plugin('enaml.workbench.core')
        view = LoadArrayView(window, task=self.task, core=core)
        window.show()

        process_app_events()

        assert_is(self.task.interface, None)

        assert_in('CSV', view.file_formats)
        self.task.selected_format = 'CSV'
        process_app_events()
        assert_is_instance(self.task.interface,
                           CSVLoadInterface)

    def test_view2(self):
        # Intantiate a view with a selected interface.
        interface = CSVLoadInterface()
        self.task.interface = interface
        self.task.selected_format = 'CSV'

        interface = self.task.interface

        window = enaml.widgets.api.Window()
        core = self.workbench.get_plugin('enaml.workbench.core')
        LoadArrayView(window, task=self.task, core=core)
        window.show()

        process_app_events()

        assert_is(self.task.interface, interface)
