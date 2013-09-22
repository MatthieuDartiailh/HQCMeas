# -*- coding: utf-8 -*-
"""
"""

from threading import Thread
import logging
from ....instruments.drivers.driver_tools import InstrIOError

def make_stoppable(function_to_decorate):
    """This decorator should be used on the process method of every task as it
    ensures that if the measurement should be stop it can be at the beginning of
    any task. This decorator must always be the first one.
    """
    def decorator(*args, **kwargs):
        if args[0].root_task.should_stop.is_set():
            return

        function_to_decorate(*args, **kwargs)
        decorator.__name__ = function_to_decorate.__name__
        decorator.__doc__ = function_to_decorate.__doc__

    return decorator


def make_parallel(process):
    """This decorator should be used when there is no need to wait for the
    process method to return to start the next task,ie the process method
    decorated don't use any data succeptible to be corrupted by the next task.
    """
    def decorator(*args, **kwargs):


        decorator.__name__ = process.__name__
        decorator.__doc__ = process.__doc__
        obj = args[0]
        thread = Thread(group = None,
                        target = process,
                        args = args,
                        kwargs = kwargs)
        threads = obj.task_database.get_value('root', 'threads')
        threads.append(thread)

        return thread.start()

    return decorator

def make_wait(process):
    """This decorator should be used when the process method need to access
    data in the database or need to be sure that physical quantities reached
    their expected values.
    """
    def decorator(*args, **kwargs):

        decorator.__name__ = process.__name__
        decorator.__doc__ = process.__doc__
        obj = args[0]
        threads = obj.task_database.get_value('root', 'threads')
        for thread in threads:
            thread.join()
        return process(*args, **kwargs)

    return decorator

def smooth_instr_crash(process, max_recursion = 10):
    """This decorator should be used on any instr task. It handles possible
    communications errors during the processing of the task. If the command
    fails it asks the immediate end of the measurement to prevent any damages
    to the sample.
    """
    def decorator(*args, **kwargs):

        decorator.__name__ = process.__name__
        decorator.__doc__ = process.__doc__
        obj = args[0]

        try:
            process(*args, **kwargs)
        except (InstrIOError) as error:
            obj.root_task.should_stop.set()
            log = logging.getLogger()
            log.critical(error.message)


    return decorator