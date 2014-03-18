# -*- coding: utf-8 -*-
from atom.api import (Atom, Str, List, ContainerList, Dict, Instance)
from collections import Counter
from ..atom_util import PrefAtom

class MonitoredEntry(PrefAtom):
    """
    """
    name = Str().tag(pref = True)
    path = Str().tag(pref = True)
    formatting = Str().tag(pref = True)
    value = Str()
    depend_on = List(Str()).tag(pref = True)
    
    def update(self, database_vals):
        vals = {d : database_vals[d] for d in self.depend_on}
        self.value = self.formatting.format(**vals)   
        
class Entry(Atom):
    """
    """
    entry = Str()
    entries = List(Str())
            
        
class EntryBuilder(Atom):
    """Used by entry creation dialog, get all database entries from monitor,
    and build the easiest to read possible list of entries mapping them to full
    database paths.
    """
    map_entries = Dict(Str(), Str())
    used_entries = ContainerList(Instance(Entry))
    formatted_entries = List(Str())
    
    def __init__(self, monitor, new_entry = None):
        
        entries = monitor.database_entries
        short_entries = [entry.rsplit('/', 1)[1] for entry in entries]
        depth = 2
        
        while self._remove_duplicates(entries, short_entries, depth):
            depth += 1
            
        self.map_entries = {short_entries[i] : entries[i] 
                                                for i in xrange(len(entries))}
        if new_entry:
            aux = self.map_entries.iteritems()
            entries = self.map_entries.keys()
            self.used_entries = [Entry(entry = key, entries = entries)
                                    for key, val in aux 
                                    if val in new_entry.depend_on]
                                        
    def format_(self, format_str):
        """
        """
        repl = ['{'+e+'}' for e in self.formatted_entries]
        return format_str.format(repl)
    
    def get_used_names(self):
        return [e.entry for e in self.used_entries]

    def _observe_used_entries(self, change):
        """
        """
        mapping = self.map_entries
        used = change['value']
        self.formatted_entries = [mapping[e.entry] for e in used 
                                            if e.entry in mapping]
        
    @staticmethod
    def _remove_duplicates(entries, short_entries, depth):
        """
        """
        duplicate = [e for e, count in Counter(short_entries).items() 
                                                            if count > 1]
        if not duplicate:
            return False
            
        for entry in duplicate:
            indexes = [i for i,x in enumerate(short_entries) if x == entry]
            for i in indexes:
                short_entries[i] = '/'.join(entries[i].split('/')[-depth:-1])
                
        return True