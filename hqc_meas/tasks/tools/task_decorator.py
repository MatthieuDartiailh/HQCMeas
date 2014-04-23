# -*- coding: utf-8 -*-
#==============================================================================
# module : task_decorator.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""

import logging
from ...instruments.drivers.driver_tools import InstrIOError


def make_stoppable(function_to_decorate):
    """ This decorator is automatically applyed the process method of every
    task as it ensures that if the measurement should be stop it can be at the
    beginning of any task. This check is performed before dealing with
    parallelism or waiting.
    """
    def decorator(*args, **kwargs):
        if args[0].root_task.should_stop.is_set():
            return False

        return function_to_decorate(*args, **kwargs)

    decorator.__name__ = function_to_decorate.__name__
    decorator.__doc__ = function_to_decorate.__doc__

    return decorator


def smooth_instr_crash(function_to_decorate):
    """This decorator should be used on any instr task. It handles possible
    communications errors during the processing of the task. If the command
    fails it asks the immediate end of the measurement to prevent any damages
    to the sample.
    """
    def decorator(*args, **kwargs):
        obj = args[0]

        try:
            return function_to_decorate(*args, **kwargs)
        except (InstrIOError) as error:
            log = logging.getLogger()
            log.error('Instrument crashed')
            log.exception(error.message)
            obj.root_task.should_stop.set()
            return False

    decorator.__name__ = function_to_decorate.__name__
    decorator.__doc__ = function_to_decorate.__doc__
    return decorator
