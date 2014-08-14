# -*- coding: utf-8 -*-
# =============================================================================
# module : while_task.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import (Str, set_default)


from ..base_tasks import ComplexTask
from .loop_exceptions import BreakException, ContinueException
from ..tools.task_decorator import handle_stop_pause

class WhileTask(ComplexTask):
    """ Task breaking out of a loop when a condition is met.

    See Python break statement documenttaion.

    """
    logic_task = True

    condition = Str().tag(pref=True)

    task_database_entries = set_default({'index' : 1})

    def check(self, *args, **kwargs):
        """

        """
        test, traceback = super(WhileTask, self).check(*args, **kwargs)

        try:
            self.format_and_eval_string(self.condition)
        except Exception as e:
            test = False
            mess = 'Task did not succeed to compute the break condition: {}'
            traceback[self.task_path + '/' + self.task_name + '-cond'] = \
                mess.format(e)

        return test, traceback

    def perform(self):
        """

        """
        i = 1
        root = self.root_task
        while True:
            self.write_in_database('index', i)
            i += 1
            if not self.format_and_eval_string(self.condition):
                break

            if handle_stop_pause(root):
                return

            try:
                for child in self.children_task:
                    child.perform_(child)
            except BreakException:
                break
            except ContinueException:
                continue

KNOWN_PY_TASKS = [WhileTask]
