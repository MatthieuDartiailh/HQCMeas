# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 16:14:30 2015

@author: lcontamin
"""

# -*- coding: utf-8 -*-
# =============================================================================
# module : test_apply_mag_field_task.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from nose.tools import (assert_equal, assert_true, assert_false, assert_in)
from nose.plugins.attrib import attr
from multiprocessing import Event
from enaml.workbench.api import Workbench

from hqc_meas.tasks.api import RootTask
from hqc_meas.tasks.tasks_instr.stepper_task import (SetSteppingParametersTask,
                                                     SteppingTask)

import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state.manifest import StateManifest
    from hqc_meas.utils.preferences.manifest import PreferencesManifest
    from hqc_meas.tasks.manager.manifest import TaskManagerManifest
    from hqc_meas.instruments.manager.manifest import InstrManagerManifest

    from hqc_meas.tasks.tasks_instr.views.stepper_view\
        import SetSteppingParametersView, SteppingView

from ...util import process_app_events, close_all_windows
from .instr_helper import InstrHelper
from ..testing_utilities import join_threads

 
class TestSetSteppingParametersTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SetSteppingParametersTask(task_name='Test')
        self.root.children_task.append(self.task)
        self.root.run_time['drivers'] = {'Test': InstrHelper}

        # This is set simply to make sure the test of InstrTask pass.
        self.task.selected_driver = 'Test'
        self.task.selected_profile = 'Test1'

    def test_check1(self):
        # Simply test that frequency, amplitude and channel can be evaluated.
        self.task.frequency = '2000'
        self.task.amplitude = '20'
        self.task.channel = None
        
        test, traceback = self.task.check(test_instr=True)
        assert_true(test)
        assert_false(traceback)

        assert_equal(self.task.get_from_database('Test_frequency'), 2000.0)
        assert_equal(self.task.get_from_database('Test_voltage'), 20.0)

    def test_check2(self):
        # Check handling a wrong frequency.
        self.task.frequency = '*1.0*'
        self.task.channel = None
        
        test, traceback = self.task.check(test_instr=True)
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test-frequency', traceback)

        assert_equal(self.task.get_from_database('Test_frequency'), 1000)

    def test_check3(self):
        # Check handling a wrong amplitude.
        self.task.amplitude = '*5*'
        self.task.channel = None
        
        test, traceback = self.task.check(test_instr=True)
        assert_false(test)
        assert_equal(len(traceback), 1)
        assert_in('root/Test-voltage', traceback)

        assert_equal(self.task.get_from_database('Test_voltage'), 15)
        
    def test_perform1(self):
        # Simple test when everything is right.
        self.task.amplitude = '10.0'
        self.task.frequency = '500'
        self.task.channel = 'id'
        
        self.root.run_time['profiles'] = \
            {'Test1': ({'anm150': [{'id': type('Dummy', (object,), {})}]}, {})}

        self.root.task_database.prepare_for_running()
        self.task.perform()
        join_threads(self.root)
        assert_equal(self.root.get_from_database('Test_frequency'), 500.0)
        assert_equal(self.root.get_from_database('Test_voltage'), 10.0)


@attr('ui')
class TestSetSteppingParametersView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(InstrManagerManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SetSteppingParametersTask(task_name='Test')
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
        view = SetSteppingParametersView(window, task=self.task, core=core)
        window.show()

        process_app_events()
        

class TestSteppingTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SteppingTask(task_name='Test')
        self.root.children_task.append(self.task)
        self.root.run_time['drivers'] = {'Test': InstrHelper}

        # This is set simply to make sure the test of InstrTask pass.
        self.task.selected_driver = 'Test'
        self.task.selected_profile = 'Test1'


    def test_check(self):
        # Check handling a wrong step number. Not in the check meth actually !
        # no real useful check
        self.task.channel = None
        
        test, traceback = self.task.check(test_instr=True)
        assert_true(test)
        assert_false(traceback)

    def test_perform(self):
        # Simple test when everything is right.
        self.task.channel = 'id'
        self.root.run_time['profiles'] = \
            {'Test1': ({'anm150': [{'id': InstrHelper(({}, 
                                                       {'step': [None]}))}]}, 
                       {})}
            
        self.root.task_database.prepare_for_running()
        self.task.perform()
        join_threads(self.root)


@attr('ui')
class TestSteppingView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(InstrManagerManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SteppingTask(task_name='Test')
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
        view = SteppingView(window, task=self.task, core=core)
        window.show()

        process_app_events()


