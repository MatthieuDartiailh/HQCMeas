# -*- coding: utf-8 -*-
#==============================================================================
# module : test_workspace.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
import enaml
from enaml.workbench.api import Workbench
import os
import shutil
import logging
from configobj import ConfigObj
from nose.tools import (assert_in, assert_not_in, assert_equal, assert_true,
                        assert_is_instance)

from hqc_meas.debug.debugger_workspace import LOG_ID
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from enaml.workbench.ui.ui_manifest import UIManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from hqc_meas.utils.pref_manifest import PreferencesManifest
    from hqc_meas.log_system.log_manifest import LogManifest
    from hqc_meas.task_management.manager_manifest import TaskManagerManifest
    from hqc_meas.instruments.manager_manifest import InstrManagerManifest
    from hqc_meas.debug.debugger_manifest import DebuggerManifest
    from hqc_meas.app_manifest import HqcAppManifest

    from .helpers import TestSuiteManifest, TestDebugger, TestDebuggerView

from ..util import complete_line, process_app_events, close_all_windows


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


class TestDebugSpace(object):

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
        self.workbench.register(DebuggerManifest())
        self.workbench.register(TestSuiteManifest())

    def teardown(self):
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        core.invoke_command(u'enaml.workbench.ui.close_workspace', {}, self)
        self.workbench.unregister(u'hqc_meas.debug')
        self.workbench.unregister(u'tests.suite')
        self.workbench.unregister(u'hqc_meas.task_manager')
        self.workbench.unregister(u'hqc_meas.instr_manager')
        self.workbench.unregister(u'hqc_meas.logging')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'hqc_meas.app')
        self.workbench.unregister(u'enaml.workbench.ui')
        self.workbench.unregister(u'enaml.workbench.core')
        close_all_windows()

    def test_life_cycle1(self):
        """ Test that workspace starting/closing goes well.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.debug')

        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.debug.workspace'},
                            self)

        log_plugin = self.workbench.get_plugin(u'hqc_meas.logging')

        # Check the plugin got the workspace
        assert_true(plugin.workspace)
        workspace = plugin.workspace

        ui = self.workbench.get_plugin('enaml.workbench.ui')
        ui.show_window()
        process_app_events()

        # Check the workspace registration.
        assert_true(workspace.log_model)
        assert_in(LOG_ID, log_plugin.handler_ids)

        logger = logging.getLogger(__name__)
        logger.info('test')
        process_app_events()
        assert_in('test', workspace.log_model.text)

        cmd = u'enaml.workbench.ui.close_workspace'
        core.invoke_command(cmd, {}, self)

        # Check the workspace removed its log handler.
        assert_not_in(LOG_ID, log_plugin.handler_ids)

        # Check the reference to the workspace was destroyed.
        assert_equal(plugin.workspace, None)

    def test_life_cycle2(self):
        """ Test that workspace reselection do restore debug panels.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.debug')

        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.debug.workspace'},
                            self)

        # Check the plugin got the workspace
        assert_true(plugin.workspace)
        workspace = plugin.workspace
        ui = self.workbench.get_plugin('enaml.workbench.ui')
        ui.show_window()
        process_app_events()

        # Creating debuggers.
        workspace.create_debugger(plugin.debuggers['debugger1'])
        process_app_events()

        workspace.create_debugger(plugin.debuggers['debugger1'])
        process_app_events()

        d_view1 = workspace.dock_area.find('item_1')
        assert_is_instance(d_view1, TestDebuggerView)
        d_view2 = workspace.dock_area.find('item_2')
        assert_is_instance(d_view2, TestDebuggerView)

        del workspace
        # Closing workspace
        cmd = u'enaml.workbench.ui.close_workspace'
        core.invoke_command(cmd, {}, self)
        process_app_events()

        # Check the debugger released their ressources.
        for debugger in plugin.debugger_instances:
            assert_true(debugger.released)

        # Reopening workspace.
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.debug.workspace'},
                            self)
        process_app_events()

        workspace = plugin.workspace

        # Checking the debuggers are there.
        dock_area = workspace.dock_area
        d_view1 = dock_area.find('item_1')
        assert_is_instance(d_view1, TestDebuggerView)
        d_view2 = dock_area.find('item_2')
        assert_is_instance(d_view2, TestDebuggerView)

    def test_create_debugger(self):
        """ Creating a debugger.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.debug')

        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.debug.workspace'},
                            self)

        # Check the plugin got the workspace
        assert_true(plugin.workspace)
        workspace = plugin.workspace
        ui = self.workbench.get_plugin('enaml.workbench.ui')
        ui.show_window()
        process_app_events()

        workspace.create_debugger(plugin.debuggers['debugger1'])
        process_app_events()

        assert_true(plugin.debugger_instances)
        assert_is_instance(plugin.debugger_instances[0], TestDebugger)

        dock_area = workspace.dock_area
        d_view = dock_area.find('item_1')
        assert_is_instance(d_view, TestDebuggerView)

    def test_closing_debugger_panel(self):
        """ Test closing a debugger panel and reopening one.

        """
        plugin = self.workbench.get_plugin(u'hqc_meas.debug')

        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': u'hqc_meas.debug.workspace'},
                            self)

        # Check the plugin got the workspace
        assert_true(plugin.workspace)
        workspace = plugin.workspace
        ui = self.workbench.get_plugin('enaml.workbench.ui')
        ui.show_window()
        process_app_events()

        workspace.create_debugger(plugin.debuggers['debugger1'])
        process_app_events()
        workspace.create_debugger(plugin.debuggers['debugger1'])
        process_app_events()
        workspace.create_debugger(plugin.debuggers['debugger1'])
        process_app_events()

        debugger = plugin.debugger_instances[1]

        item = workspace.dock_area.find('item_2')
        item.proxy.widget.close()
        process_app_events()
        item.destroy()
        process_app_events()

        assert_equal(len(workspace.dock_area.dock_items()), 3)
        assert_equal(len(plugin.debugger_instances), 2)
        assert_true(debugger.released)

        workspace.create_debugger(plugin.debuggers['debugger1'])
        process_app_events()

        assert_equal(len(plugin.debugger_instances), 3)
        assert_true(workspace.dock_area.find('item_2'))
