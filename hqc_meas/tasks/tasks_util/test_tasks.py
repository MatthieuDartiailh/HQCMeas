# -*- coding: utf-8 -*-
# =============================================================================
# module : test_task.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import (Str, Float, ContainerList, Tuple, set_default)

from time import sleep
from inspect import cleandoc
import logging

from ..base_tasks import SimpleTask
from ..tools.string_evaluation import safe_eval


class PrintTask(SimpleTask):
    """Basic task which simply prints a message in stdout. Loopable.

    """

    #: Message to print in stdout when the task is executed.
    message = Str().tag(pref=True)

    loopable = True
    task_database_entries = set_default({'message': ''})

    wait = set_default({'no_wait': []})  # Wait on all pools by default.

    def perform(self, *args, **kwargs):
        """ Format the message and print it.

        """
        mess = self.format_string(self.message)
        self.write_in_database('message', mess)
        logging.info(mess)
        return True

    def check(self, *args, **kwargs):
        """ Check that the message can be correctly formatted.

        """
        mess = self.format_string(self.message)
        self.write_in_database('message', mess)
        return True, {}


class SleepTask(SimpleTask):
    """Simply sleeps for the specified amount of time.

    Wait for any parallel operation before execution.

    """
    #: Time during which to sleep.
    time = Float().tag(pref=True)

    wait = set_default({'activated': True})  # Wait on all pools by default.

    def perform(self):
        """ Sleep.

        """
        sleep(self.time)

    def check(self, *args, **kwargs):
        return True, {}


class DefinitionTask(SimpleTask):
    """Add static values in the database.

    """
    # List of definitions.
    definitions = ContainerList(Tuple()).tag(pref=True)

    def perform(self):
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
                val = safe_eval(entry[1])
                self.write_in_database(entry[0], val)
            except Exception:
                test = False
                path = self.task_path + '/' + self.task_name + \
                    '-' + entry[0]
                traceback[path] = cleandoc('''Failed to eval definition {}
                            '''.format(entry.definition))
        return test, traceback

    def _observe_definitions(self, change):
        """ Observer adding the new definitions to the database.

        """
        self.task_database_entries = {obj[0]: 0.0
                                      for obj in change['value']}

KNOWN_PY_TASKS = [PrintTask, SleepTask, DefinitionTask]
