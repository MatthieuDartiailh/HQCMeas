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

def make_parallel(method, switch = None):
    """This decorator should be used when there is no need to wait for the
    process method to return to start the next task,ie the process method
    decorated don't use any data succeptible to be corrupted by the next task.
    """
    def decorator(method):
        if switch:
            def wrapper(self, *args, **kwargs):

                if getattr(self, switch):
                    thread = Thread(group = None,
                                    target = method,
                                    args = args,
                                    kwargs = kwargs)
                    threads = self.task_database.get_value('root', 'threads')
                    threads.append(thread)

                    return thread.start()
                else:
                    return method(*args, **kwargs)
        else:
            def wrapper(self, *args, **kwargs):

                thread = Thread(group = None,
                                target = method,
                                args = args,
                                kwargs = kwargs)
                threads = self.task_database.get_value('root', 'threads')
                threads.append(thread)

                return thread.start()

        wrapper.__name__ = method.__name__
        wrapper.__doc__ = method.__doc__
        return wrapper

    if method:
        # This was an actual decorator call, ex: @secure_communication
        return decorator(method)
    else:
        # This is a factory call, ex: @secure_communication()
        return decorator

def make_wait(method, switch = None):
    """This decorator should be used when the process method need to access
    data in the database or need to be sure that physical quantities reached
    their expected values.
    """
    def decorator(method):
        if switch:
            def wrapper(self, *args, **kwargs):

                if getattr(self, switch):
                    threads = self.task_database.get_value('root', 'threads')
                    for thread in threads:
                        thread.join()
                return method(*args, **kwargs)
        else:
            def wrapper(self, *args, **kwargs):

                threads = self.task_database.get_value('root', 'threads')
                for thread in threads:
                    thread.join()
                return method(*args, **kwargs)

        wrapper.__name__ = method.__name__
        wrapper.__doc__ = method.__doc__

        return wrapper

    if method:
        # This was an actual decorator call, ex: @secure_communication
        return decorator(method)
    else:
        # This is a factory call, ex: @secure_communication()
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
            function_to_decorate(*args, **kwargs)
        except (InstrIOError) as error:
            print 'Instrument crashed'
            log = logging.getLogger()
            log.exception(error.message)
            obj.root_task.should_stop.set()

    decorator.__name__ = function_to_decorate.__name__
    decorator.__doc__ = function_to_decorate.__doc__
    return decorator