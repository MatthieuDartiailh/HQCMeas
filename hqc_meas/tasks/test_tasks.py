# -*- coding: utf-8 -*-
"""
"""
from atom.api import (Str, Float, ContainerList, Typed, set_default, Atom)

from time import sleep
from inspect import cleandoc

from .base_tasks import SimpleTask
from .tools.database_string_formatter import get_formatted_string, safe_eval

class PrintTask(SimpleTask):
    """Basic task which simply prints a message in stdout. Loopable.
    """

    loopable = True
    task_database_entries = set_default({'message' : ''})
    message = Str().tag(pref = True)

    def __init__(self, **kwargs):
        super(PrintTask, self).__init__(**kwargs)
        self.make_wait()

    def process(self, *args, **kwargs):
        """
        """
        mess = get_formatted_string(self.message,
                                    self.task_path,
                                    self.task_database)
        self.write_in_database('message', mess)
        print mess

    def check(self, *args, **kwargs):
        """
        """
        mess = get_formatted_string(self.message,
                                    self.task_path,
                                    self.task_database)
        self.write_in_database('message', mess)
        return True, {}

class SleepTask(SimpleTask):
    """Simply sleeps for the specified amount of time. Wait for any parallel
    operation before execution.
    """

    time = Float().tag(pref = True)

    def __init__(self, **kwargs):
        super(SleepTask, self).__init__(**kwargs)
        self.make_wait()
        
    def process(self):
        """
        """
        sleep(self.time)

    def check(self, *args, **kwargs):
        """
        """
        return True, {}
        
class Definition(Atom):
    """
    """
    label = Str()
    definition = Str()

class DefinitionTask(SimpleTask):
    """Add static values in the database.
    """

    definitions = ContainerList(Typed(Definition))

    def process(self):
        """
        """
        return

    def check(self, *args, **kwargs):
        """
        """
        test = True
        traceback = {}

        for i, entry in enumerate(self.definitions):
            try:
                val = safe_eval(entry.definition)
                self.write_in_database(entry.label, val)
            except:
                test = False
                path = self.task_path + '/' + self.task_name + '-' + entry.label
                traceback[path] = cleandoc('''Failed to eval definition {}
                            '''.format(entry.definition))
        return test, traceback
        
    def register_preferences(self):
        """
        """
        super(DefinitionTask, self).register_preferences()
        self.task_preferences['definitions'] = \
            [(d.label, d.definition) for d in self.definitions]

    update_preferences_from_members = register_preferences

    def update_members_from_preferences(self, **parameters):
        """
        """
        super(DefinitionTask, self).update_members_from_preferences(
                                                                **parameters)
        if 'definitions' in parameters:
            self.definitions = [Definition(label = d[0], definition = d[1])
                                for d in parameters['definitions']]
                            
KNOWN_PY_TASKS = [PrintTask, SleepTask, DefinitionTask]