# -*- coding: utf-8 -*-
from enaml.workbench.api import Workbench
import enaml
import os
import shutil
from time import sleep
from configobj import ConfigObj
from nose.tools import (assert_in, assert_not_in, assert_equal, assert_true,
                        assert_false)

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from enaml.workbench.ui.ui_manifest import UIManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from hqc_meas.utils.pref_manifest import PreferencesManifest
    from hqc_meas.log_system.log_manifest import LogManifest
    from hqc_meas.measurement.manifest import MeasureManifest

from hqc_meas.measurement.monitors.text_monitor.monitor import TextMonitor

from ...util import complete_line, process_app_events


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


class TestMonitor(object):

    @classmethod
    def setup_class(cls):
        print complete_line(__name__ +
                            ':{}.setup_class()'.format(cls.__name__), '-', 77)

    @classmethod
    def teardown_class(cls):
        print complete_line(__name__ +
                            ':{}.teardown_class()'.format(cls.__name__), '-',
                            77)

    def setup(self):
        self.monitor = TextMonitor()

    def teardown(self):
        self.monitor = None

    def test_add_displayed_entry(self):
        """ Test adding an entry to the displayed ones.

        """
        entry = self.monitor._create_default_entry('test')
        self.monitor._displayed_entry_added(entry)

        assert_equal(self.monitor.updaters, {'test': [entry.update]})
        assert_equal(self.monitor.database_entries, ['test'])

        self.monitor._displayed_entry_added(entry)

        assert_equal(self.monitor.updaters, {'test': [entry.update,
                                                      entry.update]})
        assert_equal(self.monitor.database_entries, ['test'])

    def test_remove_displayed_entry(self):
        """ Test removing an entry from the displayed ones.

        """
        entry = self.monitor._create_default_entry('test')
        self.monitor.updaters = {'test': [entry.update, entry.update]}
        self.monitor.database_entries = ['test']

        self.monitor._displayed_entry_removed(entry)

        assert_equal(self.monitor.updaters, {'test': [entry.update]})
        assert_equal(self.monitor.database_entries, ['test'])

        self.monitor._displayed_entry_removed(entry)

        assert_equal(self.monitor.updaters, {})
        assert_equal(self.monitor.database_entries, [])

    def test_displayed_entries_observer(self):
        """ Test displayed entries observer does its job in all cases.

        """
        pass

#    def test_database_modified1(self):
#        """ Test handling the adding of an entry to the database.
#
#        """
#        pass
#
#    def test_database_modified2(self):
#        """ Test handling the adding of an entry subject to a reject rule.
#
#        """
#        pass
#
#    def test_database_modified3(self):
#        """ Test handling the adding of entries subject to a format rule.
#
#        """
#        pass
#
#    def test_database_modified4(self):
#        """ Test handling the adding of an entry enabling a custom entry.
#
#        """
#        pass
#
#    def test_database_modified5(self):
#        """ Test handling the removing of an entry.
#
#        """
#        pass
#
#    def test_refresh_monitored_entries(self):
#        """ Test refreshing entries (with a custom entry).
#
#        """
#        pass
#
#    def test_life_cycle1(self):
#        """ Test life cycle: auto_show on, proxy active on closing.
#
#        """
#        pass
#
#    def test_life_cycle2(self):
#        """ Test life cycle: auto_show off, show later, proxy active on closing
#
#        """
#        pass
#
#    def test_process_news(self):
#        """ Test processing news coming from a database.
#
#        """
#        pass
#
#    def test_clear_state(self):
#        """ Test clearing the monitor state.
#
#        """
#        pass
#
#    def test_get_state(self):
#        """ Test get_state.
#
#        """
#        pass
#
#    def test_get_editor_page(self):
#        """ Test creating the page to edit the monitor.
#
#        """
#        pass
#
#    def test_all_database_entries(self):
#        """ Test all_database_entries property.
#
#        """
#        pass
#
#
#class TestPlugin(object):
#
#    test_dir = ''
#
#    @classmethod
#    def setup_class(cls):
#        print complete_line(__name__ +
#                            ':{}.setup_class()'.format(cls.__name__), '-', 77)
#        # Creating dummy directory for prefs (avoid prefs interferences).
#        directory = os.path.dirname(__file__)
#        cls.test_dir = os.path.join(directory, '_temps')
#        os.mkdir(cls.test_dir)
#
#        # Creating dummy default.ini file in utils.
#        util_path = os.path.join(directory, '..', '..', '..', 'hqc_meas',
#                                 'utils')
#        def_path = os.path.join(util_path, 'default.ini')
#        if os.path.isfile(def_path):
#            os.rename(def_path, os.path.join(util_path, '__default.ini'))
#
#        # Making the preference manager look for info in test dir.
#        default = ConfigObj(def_path)
#        default['folder'] = cls.test_dir
#        default['file'] = 'default_test.ini'
#        default.write()
#
#        conf = ConfigObj(os.path.join(cls.test_dir, 'default_test.ini'))
#        conf.write()
#
#    @classmethod
#    def teardown_class(cls):
#        print complete_line(__name__ +
#                            ':{}.teardown_class()'.format(cls.__name__), '-',
#                            77)
#         # Removing pref files creating during tests.
#        try:
#            shutil.rmtree(cls.test_dir)
#
#        # Hack for win32.
#        except OSError:
#            print 'OSError'
#            dirs = os.listdir(cls.test_dir)
#            for directory in dirs:
#                shutil.rmtree(os.path.join(cls.test_dir), directory)
#            shutil.rmtree(cls.test_dir)
#
#        # Restoring default.ini file in utils
#        directory = os.path.dirname(__file__)
#        util_path = os.path.join(directory, '..', '..', '..', 'hqc_meas',
#                                 'utils')
#        def_path = os.path.join(util_path, 'default.ini')
#        os.remove(def_path)
#
#        aux = os.path.join(util_path, '__default.ini')
#        if os.path.isfile(aux):
#            os.rename(aux, def_path)
#
#    def setup(self):
#        pass
#
#    def teardown(self):
#        pass
#
#    def test_plugin_get_classes(self):
#        """ Test rule class request.
#
#        """
#        pass
#
#    def test_plugin_create_monitor1(self):
#        """ Test creating a default monitor using the plugin.
#
#        """
#        pass
#
#    def test_plugin_create_monitor(self):
#        """ Test creating a raw monitor using the plugin.
#
#        """
#        pass
#
#    def test_plugin_build_rule(self):
#        """ Test creating a rule using the monitor.
#
#        """
#        pass
#
#    def test_monitor_set_state(self):
#        """ Test restoring the state of a monitor.
#
#        """
#        pass
#
#    def test_add_rule_to_plugin(self):
#        """ Test adding a new rule definition to a plugin.
#
#        """
#        pass
