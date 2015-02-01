# -*- coding: utf-8 -*-
# =============================================================================
# module : log_task.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import (Str, set_default)
import logging

from ..base_tasks import SimpleTask


class LogTask(SimpleTask):
    """ Task logging a message. Loopable.

    """

    #: Message to log when the task is executed.
    message = Str().tag(pref=True)

    loopable = True
    task_database_entries = set_default({'message': ''})

    wait = set_default({'activated': True})  # Wait on all pools by default.

    def perform(self, *args, **kwargs):
        """ Format the message and log it.

        """
        mess = self.format_string(self.message)
        self.write_in_database('message', mess)
        logging.info(mess)
        return True

    def check(self, *args, **kwargs):
        """ Check that the message can be correctly formatted.

        """
        try:
            mess = self.format_string(self.message)
            self.write_in_database('message', mess)
        except Exception as e:
            mess = 'Failed to evaluate task message : {}'
            return False, {self.task_path + '/' + self.task_name:
                           mess.format(e)}

        return True, {}

KNOWN_PY_TASKS = [LogTask]
