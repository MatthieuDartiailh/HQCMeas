# -*- coding: utf-8 -*-
from enaml.workbench.api import Workbench
from enaml.widgets.api import Window
import enaml
import os
from configobj import ConfigObj
from nose.tools import (assert_in, assert_not_in, assert_equal, assert_true,
                        assert_false, assert_is, assert_dict_equal)

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from enaml.workbench.ui.ui_manifest import UIManifest
    from hqc_meas.utils.state.manifest import StateManifest
    from hqc_meas.utils.preferences.manifest import PreferencesManifest
    from hqc_meas.utils.log.manifest import LogManifest
    from hqc_meas.measurement.manifest import MeasureManifest

from hqc_meas.measurement.monitors.text_monitor.monitor import TextMonitor
from hqc_meas.measurement.monitors.text_monitor.rules import (RejectRule,
                                                              FormatRule)

from ...util import (complete_line, process_app_events, remove_tree,
                     create_test_dir)


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

    def test_create_default_entry(self):
        """ Test creating an entryt from a path.

        """
        entry = self.monitor._create_default_entry('test/entry_test', 1)
        assert_equal(entry.path, 'test/entry_test')
        assert_equal(entry.name, 'entry_test')
        assert_equal(entry.formatting, '{test/entry_test}')
        assert_equal(entry.depend_on, ['test/entry_test'])
        assert_equal(entry.value, '1')

    def test_add_displayed_entry(self):
        """ Test adding an entry to the displayed ones.

        """
        entry = self.monitor._create_default_entry('test', 1)
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
        entry = self.monitor._create_default_entry('test', 1)
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
        entry = self.monitor._create_default_entry('test', 1)
        entry2 = self.monitor._create_default_entry('test2', 2)
        # Test container operations

        # __iadd__
        self.monitor.displayed_entries += [entry]
        assert_equal(len(self.monitor.updaters['test']), 1)
        assert_equal(self.monitor.database_entries, ['test'])

        # append
        self.monitor.displayed_entries.append(entry)
        assert_equal(len(self.monitor.updaters['test']), 2)
        assert_equal(self.monitor.database_entries, ['test'])

        # insert
        self.monitor.displayed_entries.insert(0, entry)
        assert_equal(len(self.monitor.updaters['test']), 3)
        assert_equal(self.monitor.database_entries, ['test'])

        # extend
        self.monitor.displayed_entries.extend([entry])
        assert_equal(len(self.monitor.updaters['test']), 4)
        assert_equal(self.monitor.database_entries, ['test'])

        # __delitem__
        del self.monitor.displayed_entries[0]
        assert_equal(len(self.monitor.updaters['test']), 3)
        assert_equal(self.monitor.database_entries, ['test'])

        # remove
        self.monitor.displayed_entries.remove(entry)
        assert_equal(len(self.monitor.updaters['test']), 2)
        assert_equal(self.monitor.database_entries, ['test'])

        # pop
        self.monitor.displayed_entries.pop()
        assert_equal(len(self.monitor.updaters['test']), 1)
        assert_equal(self.monitor.database_entries, ['test'])

        # __setitem__
        self.monitor.displayed_entries[0] = entry2
        assert_equal(self.monitor.updaters, {'test2': [entry2.update]})
        assert_equal(self.monitor.database_entries, ['test2'])

        # Test update the whole list
        self.monitor.displayed_entries = [entry]
        assert_equal(self.monitor.updaters, {'test': [entry.update]})
        assert_equal(self.monitor.database_entries, ['test'])

    def test_database_modified1(self):
        """ Test handling the adding of an entry to the database.

        """
        self.monitor.database_modified({'value': ('test/entry_test', 1)})

        assert_equal(self.monitor.database_entries, ['test/entry_test'])
        assert_equal(len(self.monitor.displayed_entries), 1)
        assert_false(self.monitor.undisplayed_entries)
        assert_false(self.monitor.hidden_entries)
        entry = self.monitor.displayed_entries[0]
        assert_equal(entry.path, 'test/entry_test')
        assert_equal(entry.name, 'entry_test')
        assert_equal(entry.formatting, '{test/entry_test}')
        assert_equal(entry.depend_on, ['test/entry_test'])
        assert_equal(self.monitor._database_values, {'test/entry_test': 1})
        assert_in('test/entry_test', self.monitor.updaters)

    def test_database_modified2(self):
        """ Test handling the adding of an entry subject to a reject rule.

        """
        self.monitor.rules.append(RejectRule(name='Test', suffixes=['test']))
        self.monitor.database_modified({'value': ('root/make_test', 1)})

        assert_equal(self.monitor.database_entries, [])
        assert_false(self.monitor.displayed_entries)
        assert_equal(len(self.monitor.undisplayed_entries), 1)
        assert_false(self.monitor.hidden_entries)
        assert_equal(self.monitor.undisplayed_entries[0].depend_on,
                     ['root/make_test'])
        assert_equal(self.monitor._database_values, {'root/make_test': 1})
        assert_false(self.monitor.updaters)

    def test_database_modified3(self):
        """ Test handling the adding of entries subject to a format rule.

        """
        rule = FormatRule(name='Test', suffixes=['loop', 'index'],
                          new_entry_suffix='progress',
                          new_entry_formatting='{index}/{loop}')
        self.monitor.rules.append(rule)
        self.monitor.database_modified({'value': ('root/test_loop', 10)})

        assert_equal(self.monitor.database_entries, ['root/test_loop'])
        assert_equal(len(self.monitor.displayed_entries), 1)
        assert_false(self.monitor.undisplayed_entries)
        assert_false(self.monitor.hidden_entries)
        assert_equal(self.monitor.displayed_entries[0].depend_on,
                     ['root/test_loop'])
        assert_equal(self.monitor._database_values, {'root/test_loop': 10})
        assert_in('root/test_loop', self.monitor.updaters)

        self.monitor.database_modified({'value': ('root/test2_index', 1)})

        assert_equal(self.monitor.database_entries, ['root/test_loop',
                                                     'root/test2_index'])
        assert_equal(len(self.monitor.displayed_entries), 2)
        assert_false(self.monitor.undisplayed_entries)
        assert_false(self.monitor.hidden_entries)
        assert_equal(self.monitor._database_values, {'root/test_loop': 10,
                                                     'root/test2_index': 1})

        self.monitor.database_modified({'value': ('root/test_index', 1)})

        assert_equal(self.monitor.database_entries, ['root/test_loop',
                                                     'root/test2_index',
                                                     'root/test_index'])
        assert_equal(len(self.monitor.displayed_entries), 2)
        assert_false(self.monitor.undisplayed_entries)
        assert_equal(len(self.monitor.hidden_entries), 2)
        assert_equal(self.monitor._database_values, {'root/test_loop': 10,
                                                     'root/test2_index': 1,
                                                     'root/test_index': 1})
        assert_equal(len(self.monitor.updaters['root/test_loop']), 1)
        assert_equal(len(self.monitor.updaters['root/test_index']), 1)

        entry = self.monitor.displayed_entries[0]
        if entry.name != 'test_progress':
            entry = self.monitor.displayed_entries[1]

        assert_equal(entry.name, 'test_progress')
        assert_equal(entry.path, 'root/test_progress')
        assert_equal(entry.depend_on, ['root/test_loop', 'root/test_index'])
        assert_equal(entry.formatting, '{root/test_index}/{root/test_loop}')
        entry.update(self.monitor._database_values)
        process_app_events()
        assert_equal(entry.value, '1/10')

        rule.hide_entries = False
        self.monitor.database_modified({'value': ('root/test2_loop', 10)})
        assert_equal(self.monitor.database_entries, ['root/test_loop',
                                                     'root/test2_index',
                                                     'root/test_index',
                                                     'root/test2_loop'])
        assert_equal(len(self.monitor.displayed_entries), 4)
        assert_false(self.monitor.undisplayed_entries)
        assert_equal(len(self.monitor.hidden_entries), 2)
        assert_equal(self.monitor._database_values, {'root/test_loop': 10,
                                                     'root/test2_index': 1,
                                                     'root/test_index': 1,
                                                     'root/test2_loop': 10})
        assert_equal(len(self.monitor.updaters['root/test2_loop']), 2)
        assert_equal(len(self.monitor.updaters['root/test2_index']), 2)

    def test_database_modified4(self):
        """ Test handling the adding/removing an entry linked to a custom one.

        """
        entry = self.monitor._create_default_entry('test', 1)
        entry.name = 'Custom'
        entry.path = 'custom'
        entry.formatting = 'This test n {test}'
        entry.depend_on = ['test']
        self.monitor.custom_entries.append(entry)

        self.monitor.database_modified({'value': ('aux', 1)})

        assert_equal(self.monitor.database_entries, ['aux'])
        assert_equal(len(self.monitor.displayed_entries), 1)
        assert_false(self.monitor.undisplayed_entries)
        assert_false(self.monitor.hidden_entries)
        assert_equal(self.monitor._database_values, {'aux': 1})

        self.monitor.database_modified({'value': ('test', 2)})

        assert_equal(self.monitor.database_entries, ['aux', 'test'])
        assert_equal(len(self.monitor.displayed_entries), 3)
        assert_false(self.monitor.undisplayed_entries)
        assert_false(self.monitor.hidden_entries)
        assert_equal(self.monitor._database_values, {'aux': 1, 'test': 2})
        assert_equal(len(self.monitor.updaters['test']), 2)

        self.monitor.database_modified({'value': ('test',)})
        assert_equal(self.monitor.database_entries, ['aux'])
        assert_equal(len(self.monitor.displayed_entries), 1)
        assert_false(self.monitor.undisplayed_entries)
        assert_false(self.monitor.hidden_entries)
        assert_equal(self.monitor._database_values, {'aux': 1})
        assert_true(self.monitor.custom_entries)
        assert_not_in('test', self.monitor.updaters)

    def test_refresh_monitored_entries(self):
        """ Test refreshing entries (with a custom entry).

        """
        entry = self.monitor._create_default_entry('test', 1)
        entry.name = 'Custom'
        entry.path = 'custom'
        entry.formatting = 'This test n {test}'
        entry.depend_on = ['test']
        self.monitor.custom_entries.append(entry)

        self.monitor.database_modified({'value': ('test', 1)})
        self.monitor.refresh_monitored_entries({'test': 2})

        assert_equal(self.monitor.database_entries, ['test'])
        assert_equal(len(self.monitor.displayed_entries), 2)
        assert_false(self.monitor.undisplayed_entries)
        assert_false(self.monitor.hidden_entries)
        assert_equal(self.monitor._database_values, {'test': 2})

    def test_life_cycle1(self):
        """ Test life cycle: auto_show on, proxy active on closing.

        """
        assert_false(Window.windows)
        self.monitor.start(None)
        process_app_events()
        assert_true(self.monitor._view.proxy_is_active)
        assert_true(Window.windows)

        self.monitor._view.minimize()
        process_app_events()
        self.monitor.show_monitor(None)
        process_app_events()
        assert_false(self.monitor._view.is_minimized())

        self.monitor.stop()
        process_app_events()
        assert_false(Window.windows)
        assert_is(self.monitor._view, None)

    def test_life_cycle2(self):
        """ Test life cycle: auto_show off, show later, proxy active on closing

        """
        assert_false(Window.windows)
        self.monitor.auto_show = False
        self.monitor.start(None)
        process_app_events()
        assert_is(self.monitor._view, None)

        self.monitor.show_monitor(None)
        process_app_events()
        assert_true(self.monitor._view.proxy_is_active)
        assert_true(Window.windows)

        self.monitor._view.close()
        process_app_events()
        assert_false(self.monitor._view.proxy_is_active)

        self.monitor.show_monitor(None)
        process_app_events()
        assert_true(self.monitor._view.proxy_is_active)

        self.monitor.stop()
        process_app_events()
        assert_false(Window.windows)
        assert_is(self.monitor._view, None)

    def test_process_news(self):
        """ Test processing news coming from a database.

        """
        rule = FormatRule(name='Test', suffixes=['loop', 'index'],
                          new_entry_suffix='progress',
                          new_entry_formatting='{index}/{loop}',
                          hide_entries=False)
        self.monitor.rules.append(rule)
        self.monitor.database_modified({'value': ('root/test_loop', 10)})
        self.monitor.database_modified({'value': ('root/test_index', 1)})

        self.monitor.process_news(('root/test_index', 2))
        process_app_events()
        assert_equal(self.monitor.displayed_entries[0].value, '10')
        assert_equal(self.monitor.displayed_entries[1].value, '2')
        assert_equal(self.monitor.displayed_entries[2].value, '2/10')

    def test_clear_state(self):
        """ Test clearing the monitor state.

        """
        rule = FormatRule(name='Test', suffixes=['loop', 'index'],
                          new_entry_suffix='progress',
                          new_entry_formatting='{index}/{loop}')
        self.monitor.rules.append(rule)
        self.monitor.database_modified({'value': ('root/test_loop', 10)})
        self.monitor.database_modified({'value': ('root/test2_index', 1)})
        self.monitor.database_modified({'value': ('root/test_index', 1)})

        self.monitor.clear_state()
        assert_false(self.monitor.displayed_entries)
        assert_false(self.monitor.undisplayed_entries)
        assert_false(self.monitor.hidden_entries)
        assert_false(self.monitor.updaters)
        assert_false(self.monitor.custom_entries)
        assert_false(self.monitor.database_entries)

    def test_get_state(self):
        """ Test get_state.

        """
        self.monitor.measure_name = 'Test'
        entry = self.monitor._create_default_entry('test', 1)
        entry.name = 'Custom'
        entry.path = 'custom'
        entry.formatting = 'This test n {root/test_loop}*{root/test2_loop}'
        entry.depend_on = ['root/test_loop', 'root/test2_loop']
        self.monitor.custom_entries.append(entry)

        rule = FormatRule(name='Test', suffixes=['loop', 'index'],
                          new_entry_suffix='progress',
                          new_entry_formatting='{index}/{loop}')
        self.monitor.rules.append(rule)

        self.monitor.database_modified({'value': ('root/test_loop', 10)})
        self.monitor.database_modified({'value': ('root/test2_index', 1)})
        self.monitor.database_modified({'value': ('root/test_index', 1)})
        self.monitor.database_modified({'value': ('root/test2_loop', 10)})

        state = self.monitor.get_state()

        assert_in('rule_0', state)
        rule = state['rule_0']
        assert_dict_equal(rule, {'class_name': 'FormatRule', 'name': 'Test',
                                 'hide_entries': 'True',
                                 'suffixes': "['loop', 'index']",
                                 'new_entry_suffix': 'progress',
                                 'new_entry_formatting': '{index}/{loop}'})

        assert_in('custom_0', state)
        custom = state['custom_0']
        aux = {'name': 'Custom', 'path': 'custom',
               'formatting': 'This test n {root/test_loop}*{root/test2_loop}',
               'depend_on': "['root/test_loop', 'root/test2_loop']"}
        assert_dict_equal(custom, aux)

        assert_equal(state['measure_name'], 'Test')
        assert_equal(state['auto_show'], 'True')

        assert_equal(state['displayed'],
                     repr([e.path for e in self.monitor.displayed_entries]))
        assert_equal(state['undisplayed'],
                     repr([e.path for e in self.monitor.undisplayed_entries]))
        assert_equal(state['hidden'],
                     repr([e.path for e in self.monitor.hidden_entries]))

    def test_get_editor_page(self):
        """ Test creating the page to edit the monitor.

        """
        assert_true(self.monitor.get_editor_page())

    def test_all_database_entries(self):
        """ Test all_database_entries property.

        """
        test = {'test': 1, '2': 'aux'}
        self.monitor._database_values = test
        assert_equal(sorted(self.monitor.all_database_entries),
                     sorted(test.keys()))


class TestPlugin(object):

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
        util_path = os.path.join(directory, '..', '..', '..', 'hqc_meas',
                                 'utils', 'preferences')
        def_path = os.path.join(util_path, 'default.ini')

        # Making the preference manager look for info in test dir.
        default = ConfigObj(def_path)
        default['folder'] = cls.test_dir
        default['file'] = 'default_test.ini'
        default.write()

        conf = ConfigObj(os.path.join(cls.test_dir, 'default_test.ini'))
        path = u'hqc_meas.measurement.monitors.text_monitor'
        prefs = {'manifests': repr([(path, 'TextMonitorManifest')])}
        conf[u'hqc_meas.measure'] = prefs
        path = u'hqc_meas.measure.monitors.text_monitor'
        rule1 = {'class_name': 'FormatRule', 'name': 'test_format',
                 'suffixes': repr(['a', 'b']),
                 'new_entry_formatting': '{a}/{b}',
                 'new_entry_suffix': 'c'}
        rule2 = {'class_name': 'RejectRule',
                 'name': 'test_reject',
                 'suffixes': repr(['a', 'b'])}
        conf[path] = {'rules': repr({'rule1': rule1, 'rule2': rule2}),
                      'default_rules': repr(['rule1'])}

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
        util_path = os.path.join(directory, '..', '..', '..', 'hqc_meas',
                                 'utils', 'preferences')
        def_path = os.path.join(util_path, 'default.ini')
        os.remove(def_path)

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(UIManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(LogManifest())
        self.workbench.register(MeasureManifest())

        # Needed otherwise the monitor manifest is not registered.
        self.workbench.get_plugin(u'hqc_meas.measure')

    def teardown(self):
        self.workbench.unregister(u'hqc_meas.measure')
        self.workbench.unregister(u'hqc_meas.logging')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.ui')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_plugin_build_rule(self):
        """ Test building a rule.

        """
        config = {'class_name': 'RejectRule',
                  'name': 'test_reject',
                  'suffixes': repr(['a', 'b'])}
        id_pl = u'hqc_meas.measure.monitors.text_monitor'
        plugin = self.workbench.get_plugin(id_pl)
        rule = plugin.build_rule(config)

        assert_equal(rule.name, 'test_reject')
        assert_equal(rule.suffixes, ['a', 'b'])
        assert_equal(rule.__class__.__name__, 'RejectRule')

        assert_is(plugin.build_rule({'class_name': None}), None)

    def test_plugin_create_monitor1(self):
        """ Test creating a default monitor using the plugin.

        """
        id_pl = u'hqc_meas.measure.monitors.text_monitor'
        plugin = self.workbench.get_plugin(id_pl)
        monitor = plugin.create_monitor()

        assert_equal(monitor._plugin, plugin)
        assert_true(monitor.declaration)
        assert_true(monitor.rules)
        rule = monitor.rules[0]
        assert_equal(rule.__class__.__name__, 'FormatRule')
        assert_equal(rule.name, 'test_format')
        assert_equal(rule.suffixes, ['a', 'b'])
        assert_equal(rule.new_entry_formatting, '{a}/{b}')
        assert_equal(rule.new_entry_suffix, 'c')

    def test_plugin_create_monitor(self):
        """ Test creating a raw monitor using the plugin.

        """
        id_pl = u'hqc_meas.measure.monitors.text_monitor'
        plugin = self.workbench.get_plugin(id_pl)
        monitor = plugin.create_monitor(raw=True)

        assert_equal(monitor._plugin, plugin)
        assert_true(monitor.declaration)
        assert_false(monitor.rules)

    def test_monitor_set_state(self):
        """ Test restoring the state of a monitor.

        """
        id_pl = u'hqc_meas.measure.monitors.text_monitor'
        plugin = self.workbench.get_plugin(id_pl)
        monitor = plugin.create_monitor(raw=True)
        monitor.measure_name = 'Test'
        monitor.auto_show = False
        entry = monitor._create_default_entry('test', 1)
        entry.name = 'Custom'
        entry.path = 'custom'
        entry.formatting = 'This test n {root/test_loop}*{root/test2_loop}'
        entry.depend_on = ['root/test_loop', 'root/test2_loop']
        monitor.custom_entries.append(entry)

        rule = FormatRule(name='Test', suffixes=['loop', 'index'],
                          new_entry_suffix='progress',
                          new_entry_formatting='{index}/{loop}')
        monitor.rules.append(rule)

        monitor.database_modified({'value': ('root/test_loop', 10)})
        monitor.database_modified({'value': ('root/test2_index', 1)})
        monitor.database_modified({'value': ('root/test_index', 1)})
        monitor.database_modified({'value': ('root/test2_loop', 10)})

        state = monitor.get_state()
        # Atom issue of _DictProxy
        values = dict(monitor._database_values)

        monitor_rebuilt = plugin.create_monitor(raw=True)
        monitor_rebuilt.set_state(state, values)
        assert_equal(monitor_rebuilt.measure_name, 'Test')
        assert_false(monitor.auto_show)

        assert_true(monitor_rebuilt.custom_entries)
        c_entry = monitor_rebuilt.custom_entries[0]
        assert_equal(c_entry.name, entry.name)
        assert_equal(c_entry.path, entry.path)
        assert_equal(c_entry.formatting, entry.formatting)
        assert_equal(c_entry.depend_on, entry.depend_on)

        assert_true(monitor_rebuilt.rules)
        c_rule = monitor_rebuilt.rules[0]
        assert_equal(c_rule.name, rule.name)
        assert_equal(c_rule.suffixes, rule.suffixes)
        assert_equal(c_rule.new_entry_suffix, rule.new_entry_suffix)
        assert_equal(c_rule.new_entry_formatting, rule.new_entry_formatting)

        assert_equal(len(monitor_rebuilt.displayed_entries), 3)
        assert_equal(len(monitor_rebuilt.undisplayed_entries), 0)
        assert_equal(len(monitor_rebuilt.hidden_entries), 4)

    def test_add_rule_to_plugin(self):
        """ Test adding a new rule definition to a plugin.

        """
        id_pl = u'hqc_meas.measure.monitors.text_monitor'
        plugin = self.workbench.get_plugin(id_pl)
        monitor = plugin.create_monitor()

        rule = FormatRule(name='Test', suffixes=['loop', 'index'],
                          new_entry_suffix='progress',
                          new_entry_formatting='{index}/{loop}')
        monitor.rules.append(rule)

        monitor.add_rule_to_plugin('rule1')
        assert_equal(len(plugin.rules.keys()), 2)

        monitor.add_rule_to_plugin('Test')
        assert_equal(len(plugin.rules.keys()), 3)
        assert_in('Test', plugin.rules)
        rule_conf = plugin.rules['Test']
        assert_dict_equal(rule_conf, {'class_name': 'FormatRule',
                                      'name': 'Test',
                                      'hide_entries': 'True',
                                      'suffixes': repr(['loop', 'index']),
                                      'new_entry_suffix': 'progress',
                                      'new_entry_formatting': '{index}/{loop}'}
                          )
