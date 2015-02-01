# -*- coding: utf-8 -*-
# =============================================================================
# module : def_task.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import (ContainerList, Tuple)

from inspect import cleandoc

from ..base_tasks import SimpleTask
from ..tools.string_evaluation import safe_eval


class DefinitionTask(SimpleTask):
    """Add static values in the database.

    """
    # List of definitions.
    definitions = ContainerList(Tuple()).tag(pref=True)

    def perform(self):
        """ Do nothing.

        """
        pass

    def check(self, *args, **kwargs):
        """ Write all values in database.

        """
        test = True
        traceback = {}

        for i, entry in enumerate(self.definitions):
            try:
                val = safe_eval(entry[1])
                self.write_in_database(entry[0], val)
            except Exception as e:
                test = False
                path = self.task_path + '/' + self.task_name + \
                    '-' + entry[0]
                traceback[path] = cleandoc('''Failed to eval definition {}: {}
                            '''.format(entry[1], e))
        return test, traceback

    def _observe_definitions(self, change):
        """ Observer adding the new definitions to the database.

        """
        self.task_database_entries = {obj[0]: 1.0
                                      for obj in change['value']}

KNOWN_PY_TASKS = [DefinitionTask]
