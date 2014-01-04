# -*- coding: utf-8 -*-
from atom.api import (Str, ContainerList, Bool,set_default)
from .monitoring_entries import MonitoredEntry
from ..atom_util import PrefAtom

class AbstractMonitorRule(PrefAtom):
    """
    """
    name = Str().tag(pref = True)
    suffixes = ContainerList(Str()).tag(pref = True)
    
    def try_apply(self, new_entry, entries):
        """
        """
        raise NotImplementedError()
        
class RejectRule(AbstractMonitorRule):
    """
    """
    suffixes = set_default([''])
    
    def try_apply(self, new_entry, monitor):
        """
        """
        for suffix in self.suffixes:
            if new_entry.endswith(suffix):
                for entry in monitor.displayed_entries:
                    if entry.path == new_entry:
                        monitor.undisplayed_entries.append(entry)
                        monitor.displayed_entries.remove(entry)
                        break
    
class FormatRule(AbstractMonitorRule):
    """
    """
    new_entry_formatting = Str().tag(pref = True)
    new_entry_suffix = Str().tag(pref = True)
    hide_entries = Bool(True).tag(pref = True)
    
    def try_apply(self, new_entry, monitor):
        """
        """
        entries = monitor.database_entries
        for suffix in self.suffixes:
            if new_entry.endswith(suffix):
                entry_path, entry_name = new_entry.rsplit('/', 1)
                prefix = entry_path + '/' + entry_name.replace('_' + suffix, '')
                prefixed_entries = [entry for entry in entries 
                                        if entry.startswith(prefix)]
                if all(any(entry.endswith(suffix) for entry in prefixed_entries)
                            for suffix in self.suffixes):
                   
                    name_prefix = entry_name.replace('_' + suffix, '')
                    name = name_prefix + '_' + self.new_entry_suffix
                    
                    formatting = self.new_entry_formatting

                    for suffix in self.suffixes:
                        formatting = formatting.replace(suffix,
                                                        prefix + '_' + suffix)
                        
                    depend = [prefix + '_' + suffix
                                        for suffix in self.suffixes]
                    monitor.displayed_entries.append(MonitoredEntry(name = name,
                                                      formatting = formatting,
                                                      depend_on = depend)
                                                      )
                    if self.hide_entries:
                        for prefixed_entry in prefixed_entries:
                            for entry in monitor.displayed_entries:
                                if entry.path == prefixed_entry:
                                    monitor.hidden_entries.append(entry)
                                    monitor.displayed_entries.remove(entry)
                                    break
                else:
                    break
        
        return None
    
    def get_suffixes(self):
        return self.suffixes