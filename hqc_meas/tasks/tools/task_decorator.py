# -*- coding: utf-8 -*-
# =============================================================================
# module : task_decorator.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""

import logging
from time import sleep
from threading import Thread
from itertools import chain


def make_parallel(perform, pool):
    """ Machinery to execute perform_ in parallel.

    Create a wrapper around a method to execute it in a thread and
    register the thread.

    Parameters
    ----------
    perform : method
        Method which should be wrapped to run in parallel.

    pool : str
        Name of the execution pool to which the created thread belongs.

    """
    def wrapper(*args, **kwargs):

        obj = args[0]
        thread = Thread(group=None,
                        target=perform,
                        args=args,
                        kwargs=kwargs)
        all_threads = obj.task_database.get_value('root', 'threads')
        threads = all_threads.get(pool, None)
        if threads:
            threads.append(thread)
        else:
            all_threads[pool] = [thread]

        return thread.start()

    wrapper.__name__ = perform.__name__
    wrapper.__doc__ = perform.__doc__
    return wrapper


def make_wait(perform, wait, no_wait):
    """ Machinery to make perform_ wait on other tasks execution.

    Create a wrapper around a method to wait for some threads to terminate
    before calling the method. Threads are grouped in execution pools.

    Parameters
    ----------
    perform : method
        Method which should be wrapped to wait on threads.

    wait : list(str)
        Names of the execution pool which should be waited for.

    no_wait : list(str)
        Names of the execution pools which should not be waited for.

    Both parameters are mutually exlusive. If both lists are empty the
    execution will be differed till all the execution pools have completed
    their works.

    """
    if wait:
        def wrapper(*args, **kwargs):

            obj = args[0]
            all_threads = obj.task_database.get_value('root', 'threads')

            threads = chain.from_iterable([all_threads.get(w, [])
                                           for w in wait])
            for thread in threads:
                thread.join()
            all_threads.update({w: [] for w in wait if w in all_threads})

            obj.task_database.set_value('root', 'threads', all_threads)
            return perform(*args, **kwargs)

    elif no_wait:
        def wrapper(*args, **kwargs):

            obj = args[0]
            all_threads = obj.task_database.get_value('root', 'threads')

            pools = [k for k in all_threads if k not in no_wait]
            threads = chain.from_iterable([all_threads[p] for p in pools])
            for thread in threads:
                thread.join()
            all_threads.update({p: [] for p in pools})

            obj.task_database.set_value('root', 'threads', all_threads)
            return perform(*args, **kwargs)
    else:
        def wrapper(*args, **kwargs):

            obj = args[0]
            all_threads = obj.task_database.get_value('root', 'threads')

            threads = chain.from_iterable(all_threads.values())
            for thread in threads:
                thread.join()
            all_threads.update({w: [] for w in all_threads})

            obj.task_database.set_value('root', 'threads', all_threads)
            return perform(*args, **kwargs)

    wrapper.__name__ = perform.__name__
    wrapper.__doc__ = perform.__doc__

    return wrapper


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
