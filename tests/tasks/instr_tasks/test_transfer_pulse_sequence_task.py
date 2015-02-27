# -*- coding: utf-8 -*-
# =============================================================================
# module : test_transfer_pulse_sequence_task.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from nose.tools import (assert_equal, assert_true, assert_false, assert_in,
                        assert_is_instance, assert_is, assert_not_in)
from nose.plugins.attrib import attr
from multiprocessing import Event
from enaml.workbench.api import Workbench

from hqc_meas.tasks.api import RootTask
from hqc_meas.pulses.api import RootSequence, Pulse
from hqc_meas.pulses.contexts.awg_context import AWGContext
from hqc_meas.tasks.tasks_instr.transfer_pulse_sequence_task\
    import (TransferPulseSequenceTask, AWGTransferInterface)

import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state.manifest import StateManifest
    from hqc_meas.utils.preferences.manifest import PreferencesManifest
    from hqc_meas.tasks.manager.manifest import TaskManagerManifest
    from hqc_meas.instruments.manager.manifest import InstrManagerManifest
    from hqc_meas.pulses.manager.manifest import PulsesManagerManifest

    from hqc_meas.tasks.tasks_instr.views.transfer_pulse_sequence_views\
        import TransferPulseSequenceView

from ...util import process_app_events, close_all_windows
from .instr_helper import InstrHelper


class TestTransferPulseSequenceTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = TransferPulseSequenceTask(task_name='Test')
        self.root.children_task.append(self.task)
        self.root.run_time['drivers'] = {'AWG5014B': InstrHelper}
        self.root.write_in_database('int', 2)

        self.sequence = RootSequence()
        self.context = AWGContext()
        self.sequence.context = self.context
        self.sequence.external_vars = {'a': None}
        pulse1 = Pulse(def_1='1.0', def_2='{a}', channel='Ch1_M1')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='4.0', channel='Ch1_M1')
        pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10', channel='Ch1_M1')
        self.sequence.items.extend([pulse1, pulse2, pulse3])

        self.task.sequence = self.sequence
        self.task.sequence_vars = {'a': '{Root_int}'}

        interface = AWGTransferInterface(task=self.task)
        self.task.interface = interface

        self.task.selected_driver = 'AWG5014B'
        self.task.selected_profile = 'Test1'

    def test_check_no_sequence(self):
        self.task.sequence = None
        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)

    def test_check_no_interface(self):
        self.task.interface = None
        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 2)

    def test_check_errors_in_vars(self):
        self.task.sequence_vars = {'a': '**'}
        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)

    def test_check_compilation_errors(self):
        self.task.sequence.items[0].def_1 = 'b'
        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)

    def test_check_wrong_context(self):
        self.task.sequence.context = None
        test, traceback = self.task.check()
        assert_false(test)
        assert_equal(len(traceback), 1)

    def test_check_ok(self):
        test, traceback = self.task.check()
        assert_true(test)

    def test_register_preferences_seq_path(self):
        self.task.sequence_path = 'toto'
        self.task.register_preferences()
        assert_in('sequence_path', self.task.task_preferences)
        assert_not_in('sequence', self.task.task_preferences)

    def test_register_preferences_seq(self):
        self.task.register_preferences()
        assert_not_in('sequence_path', self.task.task_preferences)
        assert_in('sequence', self.task.task_preferences)


class TestAWGTransferInterface(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = TransferPulseSequenceTask(task_name='Test')
        self.root.children_task.append(self.task)
        self.root.run_time['drivers'] = {'AWG5014B': InstrHelper}
        self.root.write_in_database('int', 2)

        self.sequence = RootSequence()
        self.context = AWGContext()
        self.sequence.context = self.context
        self.sequence.external_vars = {'a': None}
        pulse1 = Pulse(def_1='1.0', def_2='{a}', channel='Ch1_M1')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='4.0', channel='Ch1_M1')
        pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10', channel='Ch1_M1')
        self.sequence.items.extend([pulse1, pulse2, pulse3])

        self.task.sequence = self.sequence
        self.task.sequence_vars = {'a': '{Root_int}'}

        interface = AWGTransferInterface(task=self.task)
        self.task.interface = interface

        self.task.selected_driver = 'AWG5014B'
        self.task.selected_profile = 'Test1'

        def get_ch(s, ch):
            return InstrHelper(({'output_state': 'OFF'},
                                {'select_sequence': lambda s, se: None}))
        prof = ({'owner': [None], 'defined_channels': ('Ch1',)},
                {'get_channel': get_ch, 'to_send': lambda s, se: None})
        self.root.run_time['profiles'] = {'Test1': prof}

    def test_perform(self):
        self.task.perform()


@attr('ui')
class TestTransferPulseSequenceView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(InstrManagerManifest())
        self.workbench.register(PulsesManagerManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = TransferPulseSequenceTask(task_name='Test')
        self.root.children_task.append(self.task)
        self.root.run_time['drivers'] = {'Test': InstrHelper}

        self.sequence = RootSequence()
        self.context = AWGContext()
        self.sequence.context = self.context
        self.sequence.external_vars = {'a': None}
        pulse1 = Pulse(def_1='1.0', def_2='{a}', channel='Ch1_M1')
        pulse2 = Pulse(def_1='{a} + 1.0', def_2='4.0', channel='Ch1_M1')
        pulse3 = Pulse(def_1='{2_stop} + 0.5', def_2='10', channel='Ch1_M1')
        self.sequence.items.extend([pulse1, pulse2, pulse3])

    def teardown(self):
        close_all_windows()

        self.workbench.unregister(u'hqc_meas.task_manager')
        self.workbench.unregister(u'hqc_meas.pulses')
        self.workbench.unregister(u'hqc_meas.instr_manager')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_view1(self):
        # Intantiate a view with no selected interface and select one after
        # Then add a sequence.
        window = enaml.widgets.api.Window()
        core = self.workbench.get_plugin('enaml.workbench.core')
        view = TransferPulseSequenceView(window, task=self.task, core=core)
        window.show()

        process_app_events()

        assert_in('AWG5014B', view.drivers)
        self.task.selected_driver = 'AWG5014B'
        process_app_events()
        assert_is_instance(self.task.interface,
                           AWGTransferInterface)

        self.task.sequence = self.sequence
        process_app_events()
        # If everything goes smoothly we are probably good.

    def test_view2(self):
        # Intantiate a view with a selected interface and a sequence.
        interface = AWGTransferInterface(task=self.task)
        self.task.interface = interface
        self.task.selected_driver = 'AWG5014B'
        self.task.sequence = self.sequence
        interface = self.task.interface

        window = enaml.widgets.api.Window()
        core = self.workbench.get_plugin('enaml.workbench.core')
        TransferPulseSequenceView(window, task=self.task, core=core)
        window.show()

        process_app_events()

        assert_is(self.task.interface, interface)
