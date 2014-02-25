# -*- coding: utf-8 -*-
"""This module is a place holder from which loop task config import the config
for the loopable task. It has to be done that way to avoid circular import"""

from ...tasks import SimpleTask
from .base_task_config import PyConfigTask

loopable_task_config = {SimpleTask: PyConfigTask}
