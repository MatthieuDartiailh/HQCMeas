# -*- coding: utf-8 -*-
#==============================================================================
# module : monitor.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from atom.api import (Instance, Value, Str, List, Dict, ForwardTyped,
                      Callable, ContainerList, Typed)
import enaml
with enaml.imports():
    from enaml.stdlib.message_box import information

from inspect import cleandoc

from ..base_monitor import BaseMonitor
from .entries import MonitoredEntry
from .rules import AbstractMonitorRule
with enaml.imports():
    from .monitor_views import (MonitorPage, MonitorView)


def import_monitor_plugin():
    """ Delayed import of the plugin to avoid circular imports.

    """
    from .text_monitor_plugin import TextMonitorPlugin
    return TextMonitorPlugin


class TextMonitor(BaseMonitor):
    """ Simple monitor displaying entries as text in widget.

    """
    # List of the entries which should be displayed when a measure is running.
    displayed_entries = ContainerList(Instance(MonitoredEntry))

    # List of the entries which should not be displayed when a measure is
    # running.
    undisplayed_entries = List(Instance(MonitoredEntry))

    # List of the entries which should be not displayed when a measure is
    # running because they would be redundant with another entry. (created by
    # a rule for example.)
    hidden_entries = List(Instance(MonitoredEntry))

    # Mapping between a database entry and a list of callable used for updating
    # an entry of the monitor which relies on the database entry.
    updaters = Dict(Str(), List(Callable()))

    # List of rules which should be used to build monitor entries.
    rules = ContainerList(Instance(AbstractMonitorRule))

    # List of user created monitor entries.
    custom_entries = List(Instance(MonitoredEntry))

    def start(self, parent_ui):
        if self.auto_show:
            self.show_monitor(parent_ui)

    def stop(self):
        if self._view.proxy_is_active:
            self.view.close()

    def process_news(self, news):
        values = self._database_values
        values[news[0]] = news[1]
        for updater in self.updaters[news[0]]:
            updater(values)

    def refresh_monitored_entries(self, entries):
        if not entries:
            entries = self._database_values.keys()[:]
        else:
            self._database_values = dict.fromkeys(entries)

        custom = self.custom_entries[:]
        self._clear_state()
        self.custom_entries = custom
        for entry in entries:
            self.database_modified({'value': (entry, 1)})

    def database_modified(self, change):
        entry = change['value']

        # Handle the addition of a new entry to the database
        if len(entry) > 1:

            # Store the new value.
            self._database_values.append(entry[1])

            # Add a default entry to the displayed monitor entries.
            self.displayed_entries.append(self._create_default_entry(entry[0]))

            # Try to apply rules.
            for rule in self.rules:
                rule.try_apply(entry[0], self)

            # Check whether any custom entry is currently hidden.
            hidden_custom = [e for e in self.custom_entries
                             if e not in self.displayed_entries
                             or e not in self.undisplayed_entries]

            # If there is one checks whether all the dependences are once
            # more available.
            if hidden_custom:
                for e in hidden_custom:
                    if all(d in self.database_entries for d in e.depend_on):
                        self.displayed_entries.append(e)

        # Handle the case of a database entry being suppressed, by removing all
        # monitors entries which where depending on this entry.
        else:
            self.displayed_entries[:] = [m for m in self.displayed_entries
                                         if entry[0] not in m.depend_on]
            self.undisplayed_entries[:] = [m for m in self.undisplayed_entries
                                           if entry[0] not in m.depend_on]
            self.hidden_entries[:] = [m for m in self.hidden_entries
                                      if entry[0] not in m.depend_on]

            if entry[0] in self.database_entries:
                self.database_entries.remove(entry[0])

    def get_state(self):
        prefs = {}
        # Save the definitions of the custom entries.
        for i, custom_entry in enumerate(self.custom_entries):
            aux = 'custom_{}'.format(i)
            prefs[aux] = custom_entry.preferences_from_members()

        # Save the definitions of the rules.
        for i, rule in enumerate(self.rules):
            aux = 'rule_{}'.format(i)
            prefs[aux] = rule.preferences_from_members()

        prefs['displayed'] = repr([e.path for e in self.displayed_entries])
        prefs['undisplayed'] = repr([e.path for e in self.undisplayed_entries])
        prefs['hidden'] = repr([e.path for e in self.hidden_entries])

        return prefs

    def set_state(self, config):
        # Request all the rules class from the plugin.
        rules_config = [conf for name, conf in config.iteritems()
                        if name.startswith('rule_')]
        class_names = [conf['class_name'] for conf in rules_config]
        rule_classes = self._plugin.request_rules_class(class_names)

        # Rebuild all rules.
        rules = []
        for rule_config in rules_config:
            rule = rule_classes[rule_config.pop('class_name')]()
            rule.update_members_from_preferences(**rule_config)
            rules.append(rule)

        self.rules = rules

        customs_config = [conf for name, conf in config.iteritems()
                          if name.startswith('custom_')]
        for custom_config in customs_config:
            entry = MonitoredEntry()
            entry.update_members_from_preferences(**custom_config)
            self.custom_entries.append(entry)

        entries = set(self.displayed_entries + self.undisplayed_entries +
                      self.hidden_entries + self.custom_entries)

        pref_disp = config['displayed']
        pref_undisp = config['undisplayed']
        pref_hidden = config['hidden']
        disp = [e for e in entries if e.path in pref_disp]
        entries -= set(disp)
        undisp = [e for e in entries if e.path in pref_undisp]
        entries -= set(undisp)
        hidden = [e for e in entries if e.path in pref_hidden]
        entries -= set(hidden)
        if entries:
            information(parent=None,
                        title='Unhandled entries',
                        text=cleandoc('''The application of new rules lead
                        to the creation of new entries. These entries has been
                        added to the displayed ones.'''))
            pref_disp += entries

        self.displayed_entries = disp
        self.undisplayed_entries = undisp
        self.hidden_entries = hidden
        self.measure_name = config['measure_name']

    def get_editor_page(self):
        return MonitorPage(monitor=self)

    def show_monitor(self, parent_ui):
        if self._view and self._view.proxy_is_active:
            self._view.restore()
        else:
            view = MonitorView(monitor=self, parent=parent_ui)
            view.show()
            self._view = view

    @property
    def all_database_entries(self):
        """ Getter returning all known database entries.

        """
        return self._database_values.keys()

    def add_rule_to_plugin(self, rule_name):
        """ Add a rule definition to the plugin.

        Parameters
        ----------
        rule_name : str
            Name of the rule whose description should be added to the plugin.

        """
        plugin = self._plugin
        if rule_name in self._plugin:
            return

        config = {}
        for rule in self.rules:
            if rule.name == rule_name:
                config = rule.preferences_from_members()
                break

        if config:
            plugin.rules[rule_name] = config

    #--- Private API ----------------------------------------------------------

    # Known values of the database entries used when recomputing an entry value
    # depending not on a single value. During edition all values are stored,
    # regardless of whether or not the entry needs to be observed, when the
    # start method is called the dict is cleaned.
    _database_values = Dict(Str(), Value())

    # Reference to the monitor plugin handling the rules persistence.
    _plugin = ForwardTyped(import_monitor_plugin)

    # Reference to the current display
    _view = Typed(MonitorView)

    @staticmethod
    def _create_default_entry(entry_path):
        """ Create a monitor entry for a database entry.

        Parameters
        ----------
        entry_path : str
            Path of the database entries for which to create a monitor entry.

        Returns
        -------
        entry : MonitoredEntry
            Monitor entry to be added to the monitor.

        """
        name = entry_path.rsplit('/', 1)[-1]
        formatting = '{' + entry_path + '}'
        return MonitoredEntry(name=name, path=entry_path,
                              formatting=formatting, depend_on=[entry_path])

    def _clear_state(self):
        """ Clear the monitor state.

        """
        with self.suppress_notifications():
            self.displayed_entries = []
            self.undisplayed_entries = []
            self.hidden_entries = []
            self.updaters = {}
            self.custom_entries = []
            self.database_entries = []

    def _observe_displayed_entries(self, change):
        """ Observer updating internals when the displayed entries change.

        This observer ensure that the list of database entries which need to
        be monitored reflects the actual needs of the monitor and that the
        monitor entries updaters mapping is up to date.

        """
        if change['type'] == 'update':
            added = set(change['value']) - set(change['oldvalue'])
            removed = set(change['oldvalue']) - set(change['value'])

            for entry in removed:
                self._displayed_entry_removed(entry)
            for entry in added:
                self._displayed_entry_added(entry)

        elif change['type'] == 'container':
            op = change['operation']
            if op in ('__iadd__', 'append', 'extend', 'insert'):
                if 'item' in change:
                    self._displayed_entry_added(change['item'])
                if 'items' in change:
                    for entry in change['items']:
                        self._displayed_entry_added(entry)

            elif op in ('__delitem__', 'remove', 'pop'):
                if 'item' in change:
                    self._displayed_entry_removed(change['item'])
                if 'items' in change:
                    for entry in change['items']:
                        self._displayed_entry_removed(entry)

            elif op in '__setitem__':
                old = change['olditem']
                if isinstance(old, list):
                    for entry in old:
                        self._displayed_entry_removed(entry)
                else:
                    self._displayed_entry_removed(old)

                new = change['newitem']
                if isinstance(new, list):
                    for entry in new:
                        self._displayed_entry_added(entry)
                else:
                    self._displayed_entry_added(new)

    def _displayed_entry_added(self, entry):
        """ Tackle the addition of a displayed monitor entry.

        First this method will add the entry updater into the updaters dict for
        each of its dependence and if one dependence is absent from the
        database_entries it will be added.

        Parameters
        ----------
        entry : MonitoredEntry
            The entry being added to the list of displayed entries of the
            monitor.

        """
        for dependence in entry.depend_on:
            if dependence in self.updaters:
                self.updaters[dependence].append(entry.update)
            else:
                self.updaters[dependence] = [entry.update]

            if dependence not in self.database_entries:
                self.database_entries.append(dependence)

    def _displayed_entry_removed(self, entry):
        """ Tackle the deletion of a displayed monitor entry.

        First this method will remove the entry updater for each of its
        dependence and no updater remain for that database entry, the entry
        will be removed from the database_entries

        Parameters
        ----------
        entry : MonitoredEntry
            The entry being added to the list of displayed entries of the
            monitor.

        """
        for dependence in entry.depend_on:
            self.updaters[dependence].remove(entry.update)

            if not self.updaters[dependence]:
                del self.updaters[dependence]
                self.database_entries.remove(dependence)
