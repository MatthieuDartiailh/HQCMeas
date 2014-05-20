# -*- coding: utf-8 -*-
#==============================================================================
# module : test_task.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from atom.api import (Str, Float, ContainerList, Tuple, set_default)

from time import sleep
from inspect import cleandoc

from ..base_tasks import SimpleTask
from ..tools.database_string_formatter import get_formatted_string, safe_eval


class PrintTask(SimpleTask):
    """Basic task which simply prints a message in stdout. Loopable.

    """

    # Message to print in stdout when the task is executed.
    message = Str().tag(pref=True)

    loopable = True
    task_database_entries = set_default({'message': ''})

    def __init__(self, **kwargs):
        super(PrintTask, self).__init__(**kwargs)
        self.make_wait()

    def process(self, *args, **kwargs):
        """ Format the message and print it.

        """
        mess = get_formatted_string(self.message,
                                    self.task_path,
                                    self.task_database)
        self.write_in_database('message', mess)
        print mess
        return True

    def check(self, *args, **kwargs):
        """ Check that the message can be correctly formatted.

        """
        mess = get_formatted_string(self.message,
                                    self.task_path,
                                    self.task_database)
        self.write_in_database('message', mess)
        return True, {}


class SleepTask(SimpleTask):
    """Simply sleeps for the specified amount of time.

    Wait for any parallel operation before execution.

    """
    # Time during which to sleep.
    time = Float().tag(pref=True)

    def __init__(self, **kwargs):
        super(SleepTask, self).__init__(**kwargs)
        self.make_wait()

    def process(self):
        """ Sleep.
        """
        sleep(self.time)
        return True

    def check(self, *args, **kwargs):
        return True, {}


class DefinitionTask(SimpleTask):
    """Add static values in the database.

    """
    # List of definitions.
    definitions = ContainerList(Tuple()).tag(pref=True)

    def process(self):
        """ Do nothing.
        """
        return True

    def check(self, *args, **kwargs):
        """ Write all values in database.

        """
        test = True
        traceback = {}

        for i, entry in enumerate(self.definitions):
            try:
                val = safe_eval(entry.definition)
                self.write_in_database(entry.label, val)
            except Exception:
                test = False
                path = self.task_path + '/' + self.task_name + \
                    '-' + entry.label
                traceback[path] = cleandoc('''Failed to eval definition {}
                            '''.format(entry.definition))
        return test, traceback

    def _observe_definitions(self, change):
        """ Observer adding the new definitions to the database.

        """
        self.task_database_entries = {obj[0]: 0.0
                                      for obj in change['value']}

KNOWN_PY_TASKS = [PrintTask, SleepTask, DefinitionTask]
