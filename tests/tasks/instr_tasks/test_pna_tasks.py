# -*- coding: utf-8 -*-
# =============================================================================
# module : test_rf_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from nose.tools import (assert_equal, assert_true, assert_false, assert_in,
                        assert_is_instance, assert_is)
from nose.plugins.attrib import attr
from multiprocessing import Event
from enaml.workbench.api import Workbench

from hqc_meas.tasks.api import RootTask
from hqc_meas.tasks.tasks_instr.rf_tasks\
    import (SetRFFrequencyTask, SetRFPowerTask)
from hqc_meas.tasks.tasks_instr.pna_tasks\
    import (PNASetRFFrequencyInterface, PNASetRFPowerInterface,
            PNASinglePointMeasureTask, PNASweepTask)

import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state.manifest import StateManifest
    from hqc_meas.utils.preferences.manifest import PreferencesManifest
    from hqc_meas.tasks.manager.manifest import TaskManagerManifest
    from hqc_meas.instruments.manager.manifest import InstrManagerManifest

    from hqc_meas.tasks.tasks_instr.views.rf_views\
        import (RFFrequencyView, RFPowerView)
    from hqc_meas.tasks.tasks_instr.views.pna_task_views\
        import (PNASinglePointView, PNASweepMeasView)

from ...util import process_app_events, close_all_windows
from .instr_helper import InstrHelper


class TestPNASetRFFrequencyTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SetRFFrequencyTask(task_name='Test')
        self.root.children_task.append(self.task)
        self.root.run_time['drivers'] = {'Test': InstrHelper}

        self.task.unit = 'GHz'

        # This is set simply to make sure the test of InstrTask pass.
        self.task.selected_driver = 'Test'
        self.task.selected_profile = 'Test1'

    def test_check_pna_interface1(self):
        # Simply test that everything is ok if frequency can be evaluated.
        self.task.interface = PNASetRFFrequencyInterface(task=self.task,
                                                         channel=1)
        self.task.frequency = '1.0'

        profile = {'Test1': ({'defined_channels': [[1]]},
                             {})}
        self.root.run_time['profiles'] = profile

        test, traceback = self.task.check(test_instr=True)
        assert_true(test)
        assert_false(traceback)

    def test_check_pna_interface2(self):
        # Check handling a wrong channel.
        self.task.interface = PNASetRFFrequencyInterface(task=self.task,
                                                         channel=1)
        self.task.frequency = '1.0'

        profile = {'Test1': ({'defined_channels': [[2]]},
                             {})}
        self.root.run_time['profiles'] = profile

        test, traceback = self.task.check(test_instr=True)
        assert_false(test)
        assert_equal(len(traceback), 1)

    def test_perform_pna_interface(self):
        self.task.interface = PNASetRFFrequencyInterface(task=self.task)
        self.task.frequency = '1.0'

        profile = {'Test1': ({'frequency': [0.0],
                              'owner': [None]},
                             {'get_channel': lambda x, i: x}
                             )}
        self.root.run_time['profiles'] = profile

        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_frequency'), 1.0e9)


@attr('ui')
class TestPNASetRFFrequencyView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(InstrManagerManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SetRFFrequencyTask(task_name='Test')
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
        view = RFFrequencyView(window, task=self.task, core=core)
        window.show()

        process_app_events()

        assert_in('AgilentPNA', view.drivers)
        self.task.selected_driver = 'AgilentPNA'
        process_app_events()
        assert_is_instance(self.task.interface, PNASetRFFrequencyInterface)

    def test_view2(self):
        # Intantiate a view with a selected interface.
        self.task.interface = PNASetRFFrequencyInterface(task=self.task)
        self.task.frequency = '1.0'
        self.task.selected_driver = 'AgilentPNA'

        interface = self.task.interface

        window = enaml.widgets.api.Window()
        core = self.workbench.get_plugin('enaml.workbench.core')
        RFFrequencyView(window, task=self.task, core=core)
        window.show()

        process_app_events()

        assert_is(self.task.interface, interface)


class TestPNASetRFPowerTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SetRFPowerTask(task_name='Test')
        self.root.children_task.append(self.task)
        self.root.run_time['drivers'] = {'Test': InstrHelper}

        # This is set simply to make sure the test of InstrTask pass.
        self.task.selected_driver = 'Test'
        self.task.selected_profile = 'Test1'

    def test_check_pna_interface1(self):
        # Simply test that everything is ok if power can be evaluated.
        self.task.interface = PNASetRFPowerInterface(task=self.task,
                                                     channel=1)
        self.task.power = '1.0'
        profile = {'Test1': ({'defined_channels': [[1]]},
                             {})}
        self.root.run_time['profiles'] = profile

        test, traceback = self.task.check(test_instr=True)
        assert_true(test)
        assert_false(traceback)

    def test_check_pna_interface2(self):
        # Check handling a wrong channel.
        self.task.interface = PNASetRFPowerInterface(task=self.task,
                                                     channel=2)
        self.task.power = '1.0'
        profile = {'Test1': ({'defined_channels': [[1]]},
                             {})}
        self.root.run_time['profiles'] = profile

        test, traceback = self.task.check(test_instr=True)
        assert_false(test)
        assert_equal(len(traceback), 1)

    def test_perform_pna_interface(self):
        self.task.interface = PNASetRFPowerInterface(task=self.task,
                                                     channel=1)
        self.task.power = '1.0'

        profile = {'Test1': ({'power': [0.0],
                              'port': [1],
                              'owner': [None]},
                             {'get_channel': lambda x, i: x}
                             )}
        self.root.run_time['profiles'] = profile
        self.root.task_database.prepare_for_running()

        self.task.perform()
        assert_equal(self.root.get_from_database('Test_power'), 1.0)


@attr('ui')
class TestPNASetRFPowerView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(InstrManagerManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SetRFPowerTask(task_name='Test')
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
        view = RFPowerView(window, task=self.task, core=core)
        window.show()

        process_app_events()

        assert_in('AgilentPNA', view.drivers)
        self.task.selected_driver = 'AgilentPNA'
        process_app_events()
        assert_is_instance(self.task.interface, PNASetRFPowerInterface)

    def test_view2(self):
        # Intantiate a view with a selected interface.
        self.task.interface = PNASetRFPowerInterface(task=self.task)
        self.task.power = '1.0'
        self.task.selected_driver = 'AgilentPNA'

        interface = self.task.interface

        window = enaml.widgets.api.Window()
        core = self.workbench.get_plugin('enaml.workbench.core')
        RFPowerView(window, task=self.task, core=core)
        window.show()

        process_app_events()

        assert_is(self.task.interface, interface)


class TestPNASinglePointMeasureTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = PNASinglePointMeasureTask(task_name='Test')
        self.root.children_task.append(self.task)
        self.root.run_time['drivers'] = {'Test': InstrHelper}

        # This is set simply to make sure the test of InstrTask pass.
        self.task.selected_driver = 'Test'
        self.task.selected_profile = 'Test1'

    def test_measure_observation(self):
        pass

    def test_check1(self):
        # Simply test that everything is ok.
        self.task.measures = [('S21', ''), ('S33', 'MLIN')]

        profile = {'Test1': ({'defined_channels': [[1]]},
                             {})}
        self.root.run_time['profiles'] = profile

        test, traceback = self.task.check(test_instr=True)
        assert_true(test)
        assert_false(traceback)

    def test_check2(self):
        # Check handling a wrong channel.
        self.task.measures = [('S21', ''), ('S33', 'MLIN')]

        profile = {'Test1': ({'defined_channels': [[3]]},
                             {})}
        self.root.run_time['profiles'] = profile

        test, traceback = self.task.check(test_instr=True)
        assert_false(test)
        assert_equal(len(traceback), 1)

    def test_check3(self):
        # Check handling a wrong S parameter.
        self.task.measures = [('S21', ''), ('SF3', 'MLIN')]

        profile = {'Test1': ({'defined_channels': [[1]]},
                             {})}
        self.root.run_time['profiles'] = profile

        test, traceback = self.task.check(test_instr=True)
        assert_false(test)
        assert_equal(len(traceback), 1)

#    def test_perform(self):
#        self.task.measures = [('S21', ''), ('S33', 'MLIN')]
#
#        profile = {'Test1': ({'defined_channels': [[1]]},
#                             {})}
#        self.root.run_time['profiles'] = profile
#
#        self.root.task_database.prepare_for_running()
#
#        self.task.perform()
#        assert_equal(self.root.get_from_database('Test_output'), 1.0)


#@attr('ui')
#class TestPNASinglePointMeasureView(object):
#
#    def setup(self):
#        self.workbench = Workbench()
#        self.workbench.register(CoreManifest())
#        self.workbench.register(StateManifest())
#        self.workbench.register(PreferencesManifest())
#        self.workbench.register(InstrManagerManifest())
#        self.workbench.register(TaskManagerManifest())
#
#        self.root = RootTask(should_stop=Event(), should_pause=Event())
#        self.task = PNASinglePointMeasureTask(task_name='Test')
#        self.root.children_task.append(self.task)
#        self.root.run_time['drivers'] = {'Test': InstrHelper}
#
#    def teardown(self):
#        close_all_windows()
#
#        self.workbench.unregister(u'hqc_meas.task_manager')
#        self.workbench.unregister(u'hqc_meas.instr_manager')
#        self.workbench.unregister(u'hqc_meas.preferences')
#        self.workbench.unregister(u'hqc_meas.state')
#        self.workbench.unregister(u'enaml.workbench.core')
#
#    def test_view1(self):
#        # Intantiate a view with no selected interface and select one after
#        window = enaml.widgets.api.Window()
#        core = self.workbench.get_plugin('enaml.workbench.core')
#        view = PNASinglePointView(window, task=self.task, core=core)
#        window.show()
#
#        process_app_events()
#
#        assert_in('AgilentE8257D', view.drivers)
#        self.task.selected_driver = 'AgilentE8257D'
#        process_app_events()
#
#    def test_view2(self):
#        # Intantiate a view with a selected interface.
#        self.task.switch = '1.0'
#        self.task.selected_driver = 'AgilentE8257D'
#
#        interface = self.task.interface
#
#        window = enaml.widgets.api.Window()
#        core = self.workbench.get_plugin('enaml.workbench.core')
#        PNASinglePointView(window, task=self.task, core=core)
#        window.show()
#
#        process_app_events()
#
#        assert_is(self.task.interface, interface)
#
#
#class TestPNASweepTask(object):
#
#    def setup(self):
#        self.root = RootTask(should_stop=Event(), should_pause=Event())
#        self.task = PNASweepTask(task_name='Test')
#        self.root.children_task.append(self.task)
#        self.root.run_time['drivers'] = {'Test': InstrHelper}
#
#        # This is set simply to make sure the test of InstrTask pass.
#        self.task.selected_driver = 'Test'
#        self.task.selected_profile = 'Test1'
#
#    def test_check1(self):
#        # Simply test that everything is ok if voltage can be evaluated.
#        self.task.switch = '1.0'
#
#        test, traceback = self.task.check(test_instr=True)
#        assert_true(test)
#        assert_false(traceback)
#
#    def test_check2(self):
#        # Check handling a wrong voltage.
#        self.task.switch = '*1.0*'
#
#        test, traceback = self.task.check(test_instr=True)
#        assert_false(test)
#        assert_equal(len(traceback), 1)
#
#    def test_perform(self):
#        self.task.switch = '1.0'
#
#        self.root.run_time['profiles'] = {'Test1': ({'output': [0.0],
#                                                     'owner': [None]}, {})}
#
#        self.root.task_database.prepare_for_running()
#
#        self.task.perform()
#        assert_equal(self.root.get_from_database('Test_output'), 1.0)
#
#
#@attr('ui')
#class TestPNASweepView(object):
#
#    def setup(self):
#        self.workbench = Workbench()
#        self.workbench.register(CoreManifest())
#        self.workbench.register(StateManifest())
#        self.workbench.register(PreferencesManifest())
#        self.workbench.register(InstrManagerManifest())
#        self.workbench.register(TaskManagerManifest())
#
#        self.root = RootTask(should_stop=Event(), should_pause=Event())
#        self.task = PNASweepTask(task_name='Test')
#        self.root.children_task.append(self.task)
#        self.root.run_time['drivers'] = {'Test': InstrHelper}
#
#    def teardown(self):
#        close_all_windows()
#
#        self.workbench.unregister(u'hqc_meas.task_manager')
#        self.workbench.unregister(u'hqc_meas.instr_manager')
#        self.workbench.unregister(u'hqc_meas.preferences')
#        self.workbench.unregister(u'hqc_meas.state')
#        self.workbench.unregister(u'enaml.workbench.core')
#
#    def test_view1(self):
#        # Intantiate a view with no selected interface and select one after
#        window = enaml.widgets.api.Window()
#        core = self.workbench.get_plugin('enaml.workbench.core')
#        view = PNASweepMeasView(window, task=self.task, core=core)
#        window.show()
#
#        process_app_events()
#
#        assert_in('AgilentE8257D', view.drivers)
#        self.task.selected_driver = 'AgilentE8257D'
#        process_app_events()
#
#    def test_view2(self):
#        # Intantiate a view with a selected interface.
#        self.task.switch = '1.0'
#        self.task.selected_driver = 'AgilentE8257D'
#
#        interface = self.task.interface
#
#        window = enaml.widgets.api.Window()
#        core = self.workbench.get_plugin('enaml.workbench.core')
#        PNASweepMeasView(window, task=self.task, core=core)
#        window.show()
#
#        process_app_events()
#
#        assert_is(self.task.interface, interface)
