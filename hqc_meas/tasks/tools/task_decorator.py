# -*- coding: utf-8 -*-
#==============================================================================
# module : task_decorator.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""

import logging
from time import sleep


def make_stoppable(function_to_decorate):
    """ This decorator is automatically applyed the process method of every
    task as it ensures that if the measurement should be stop it can be at the
    beginning of any task. This check is performed before dealing with
    parallelism or waiting.
    """
    def decorator(*args, **kwargs):
        stop_flag = args[0].root_task.should_stop
        if stop_flag.is_set():
            return

        pause_flag = args[0].root_task.should_pause
        while pause_flag.is_set():
            sleep(0.05)
            if stop_flag.is_set():
                return

        return function_to_decorate(*args, **kwargs)

    decorator.__name__ = function_to_decorate.__name__
    decorator.__doc__ = function_to_decorate.__doc__

    return decorator


def smooth_crash(function_to_decorate):
    """This decorator is automatically applied to all perform function. It
    ensures that any unhandled error will cause the measure to stop in a nice
    way.
    """
    def decorator(*args, **kwargs):
        obj = args[0]

        try:
            return function_to_decorate(*args, **kwargs)
        except Exception:
            log = logging.getLogger(__name__)
            mes = 'The following unhandled exception occured in {} :'
            log.exception(mes.format(obj.task_name))
            obj.root_task.should_stop.set()

    decorator.__name__ = function_to_decorate.__name__
    decorator.__doc__ = function_to_decorate.__doc__
    return decorator
