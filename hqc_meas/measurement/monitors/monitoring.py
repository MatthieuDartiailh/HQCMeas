# -*- coding: utf-8 -*-

from threading import Thread
from atom.api import (Atom, Instance, Value, Str, List, Dict,
                      Callable, ContainerList)
import enaml
with enaml.imports():
    from enaml.stdlib.message_box import information

from inspect import cleandoc
from configobj import ConfigObj
import os

from ..atom_util import tagged_members
from .monitoring_entries import MonitoredEntry
from .monitoring_rules import AbstractMonitorRule
from . import monitoring_rules


class MeasureMonitor(Atom):

    """
    """
    displayed_entries = ContainerList(Instance(MonitoredEntry))
    undisplayed_entries = ContainerList(Instance(MonitoredEntry))
    hidden_entries = List(Instance(MonitoredEntry))

    updaters = Dict(Str(), List(Callable()))
    database_values = Dict(Str(), Value())
    _temp = Value()

    monitoring_thread = Instance(Thread)
    status = Str('READY')
    measure_name = Str()

    rules = ContainerList(Instance(AbstractMonitorRule))
    custom_entries = List(Instance(MonitoredEntry))
    database_entries = List(Str())

    def __init__(self):
        super(MeasureMonitor, self).__init__()
        self.load_rules()

    def map_news(self, news):
        """
        """
        values = self.database_values
        values[news[0]] = news[1]
        for updater in self.updaters[news[0]]:
            updater(values)

    def start(self, queue):
        """
        """
        self.monitoring_thread = ThreadMeasureMonitor(queue, self)
        self.monitoring_thread.start()

    def stop(self):
        """
        """
        self.monitoring_thread.join()

    def clear_state(self):
        """
        """
        with self.suppress_notifications():
            self.displayed_entries = []
            self.undisplayed_entries = []
            self.hidden_entries = []
            self.updaters = {}
            self.database_values = {}
            self._temp = None
            self.custom_entries = []
            self.database_entries = []

    def refresh_monitored_entries(self, change=None):
        """Handle the case of a rule modification leading to regenerating all
        entries, react to update or container"""
        if change is None or change['type'] in ('update', 'container'):
            old = self.database_entries[:]
            custom = self.custom_entries[:]
            self.clear_state()
            self.custom_entries = custom
            for entry in old:
                self.database_modified({'value': (entry, 1)})

    def database_modified(self, change):
        """
        Handler which should be connected to the database notifier during
        edition"""
        entry = change['value']

        # Handle the addition of a new entry to the database
        if len(entry) > 1:
            self._temp = entry[1]
            self.database_entries.append(entry[0])
            self.displayed_entries.append(self._create_default_entry(entry[0]))
            for rule in self.rules:
                rule.try_apply(entry[0], self)
            hidden_custom = [e for e in self.custom_entries
                             if e not in self.displayed_entries
                             or e not in self.undisplayed_entries]
            if hidden_custom:
                for e in hidden_custom:
                    if all(d in self.database_entries for d in e.depend_on):
                        self.displayed_entries.append(e)

        # Handle the case of a database entry being suppressed
        else:
            self.displayed_entries[:] = [m for m in self.displayed_entries
                                         if entry[0] not in m.depend_on]
            self.undisplayed_entries[:] = [m for m in self.undisplayed_entries
                                           if entry[0] not in m.depend_on]
            self.hidden_entries[:] = [m for m in self.hidden_entries
                                      if entry[0] not in m.depend_on]
            self.database_entries.remove(entry[0])

    def save_rules(self, change):
        """
        """
        if change['value']:
            path = os.path.join(os.path.dirname(__file__), 'rules.ini')
            config = ConfigObj(path, indent_type='    ')
            for i, rule in enumerate(self.rules):
                pref = {name: str(getattr(rule, name))
                        for name in tagged_members(rule, 'pref')}
                pref['class'] = rule.__class__.__name__
                config['rule{}'.format(i)] = pref
            config.write()

    def load_rules(self):
        """
        """
        path = os.path.join(os.path.dirname(__file__), 'rules.ini')
        if os.path.isfile(path):
            config = ConfigObj(path)
            with self.suppress_notifications():
                for rule_pref in config.itervalues():
                    class_name = rule_pref.pop('class')
                    rule = getattr(monitoring_rules, class_name)()
                    rule.update_members_from_preferences(**rule_pref)
                    self.rules.append(rule)

    def save_monitor_state(self):
        """
        """
        pref = {}
        cust = []
        for e in enumerate(self.custom_entries):
            cust.append({name: str(getattr(e, name))
                         for name in tagged_members(e, 'pref')})
        pref['custom'] = cust
        pref['displayed'] = [e.path for e in self.displayed_entries]
        pref['undisplayed'] = [e.path for e in self.undisplayed_entries]
        pref['hidden'] = [e.path for e in self.hidden_entries]
        pref['measure_name'] = self.measure_name

        return pref

    def load_monitor_state(self, config):
        """
        """
        if 'custom' in config:
            for e in config['custom']:
                entry = MonitoredEntry()
                entry.update_members_from_preferences(**e)
                self.custom_entries.append[entry]

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
            pass
        self.displayed_entries = disp
        self.undisplayed_entries = undisp
        self.hidden_entries = hidden
        self.measure_name = config['measure_name']

    @staticmethod
    def _create_default_entry(entry_path):
        """
        """
        name = entry_path.rsplit('/', 1)[-1]
        formatting = '{' + entry_path + '}'
        return MonitoredEntry(name=name, path=entry_path,
                              formatting=formatting, depend_on=[entry_path])

    def _observe_displayed_entries(self, change):
        """
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

            elif op in ('__setitem__'):
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
        """
        """
        for dependence in entry.depend_on:
            if dependence in self.updaters:
                self.updaters[dependence].append(entry.update)
            else:
                self.updaters[dependence] = [entry.update]

            if dependence not in self.database_values:
                self.database_values[dependence] = self._temp

    def _displayed_entry_removed(self, entry):
        """
        """
        for dependence in entry.depend_on:
            self.updaters[dependence].remove(entry.update)

            if not self.updaters[dependence]:
                del self.updaters[dependence]
                del self.database_values[dependence]
