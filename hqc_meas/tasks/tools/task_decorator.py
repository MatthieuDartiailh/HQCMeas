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
from threading import Thread, current_thread
from itertools import chain


def handle_stop_pause(root):
    """ Check the state of the stop and pause event and handle the pause.

    When the pause stops the main thread take care of re-initializing the
    driver owners (so that any user modification shoudl not cause a crash) and
    signal the other threads it is done by settibg the resume flag.

    Parameters
    ----------
    root : RootTask
        RootTask of the hierarchy.

    Returns
    -------
    exit : bool or None
        Whether or not the function returned because should_stop was set.

    """
    stop_flag = root.should_stop
    if stop_flag.is_set():
        return True

    pause_flag = root.should_pause
    if pause_flag.is_set():
        root.resume.clear()
        root.paused_threads_counter.increment()
        while True:
            sleep(0.05)
            if stop_flag.is_set():
                root.paused_threads_counter.decrement()
                return True
            if not pause_flag.is_set():
                if current_thread().name == 'MainThread':
                    # Prevent some issues if a stupid user changes a
                    # value on an instr previously set by a task.
                    instrs = root.instrs
                    for instr_id in instrs:
                        instrs[instr_id].owner = ''
                    root.resume.set()
                    root.paused_threads_counter.decrement()
                    break
                else:
                    # Safety here ensuring the main thread finished
                    # re-initializing the instr.
                    root.resume.wait()
                    root.paused_threads_counter.decrement()
                    break


def make_stoppable(function_to_decorate):
    """ This decorator is automatically applyed the process method of every
    task as it ensures that if the measurement should be stop it can be at the
    beginning of any task. This check is performed before dealing with
    parallelism or waiting.

    """
    def decorator(*args, **kwargs):

        if handle_stop_pause(args[0].root_task):
            return

        return function_to_decorate(*args, **kwargs)

    decorator.__name__ = function_to_decorate.__name__
    decorator.__doc__ = function_to_decorate.__doc__

    return decorator


def smooth_crash(function_to_decorate):
    """ This decorator ensures that any unhandled error will cause the measure
    to stop in a nice way. It is always present at the root call of any thread.

    """
    def decorator(*args, **kwargs):
        obj = args[0]

        try:
            return function_to_decorate(*args, **kwargs)
        except Exception:
            log = logging.getLogger(function_to_decorate.__module__)
            mes = 'The following unhandled exception occured in {} :'
            log.exception(mes.format(obj.task_name))
            obj.root_task.should_stop.set()

    decorator.__name__ = function_to_decorate.__name__
    decorator.__doc__ = function_to_decorate.__doc__
    return decorator


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
        root = obj.root_task
        safe_perform = smooth_crash(perform)
        thread = Thread(group=None,
                        target=safe_perform,
                        args=args,
                        kwargs=kwargs)
        # Create a shallow copy to avoid mutating a dict shared by multiple
        # threads.
        pools = obj.root_task.threads
        with pools.safe_access(pool) as threads:
            threads.append(thread)

        root.active_threads_counter.increment()
        thread.start()
        root.active_threads_counter.decrement()

    wrapper.__name__ = perform.__name__
    wrapper.__doc__ = perform.__doc__
    return wrapper


# XXXX should now support nested wait in parallel
def make_wait(perform, wait, no_wait):
    """ Machinery to make perform_ wait on other tasks execution.

    Create a wrapper around a method to wait for some threads to terminate
    before calling the method. Threads are grouped in execution pools.
    This method supports new threads being started while it is waiting.

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
            all_threads = obj.root_task.threads
            while True:
                # Get all the threads we should be waiting upon.
                threads = chain.from_iterable([all_threads[w]
                                               for w in wait])

                # If there is none break. Use any as threads is an iterator.
                if not any(threads):
                    break

                # Else join them.
                for thread in threads:
                    thread.join()

                # Make sure nobody modify the pools and update them by removing
                # the references to the dead threads.
                with all_threads.locked():
                    for w in wait:
                        all_threads[w] = [t for t in all_threads[w]
                                          if t.is_alive()]

                # Start over till no thread remain in the pool in wait.

            return perform(*args, **kwargs)

    elif no_wait:
        def wrapper(*args, **kwargs):

            obj = args[0]
            # Create a shallow copy to avoid mutating a dict shared by multiple
            # threads.
            all_threads = obj.root_task.threads
            pools = [k for k in all_threads if k not in no_wait]
            while True:
                # Get all the threads we should be waiting upon.
                threads = chain.from_iterable([all_threads[p]
                                               for p in pools])

                # If there is None break. Use any as threads is an iterator.
                if not any(threads):
                    break

                # Else join them.
                for thread in threads:
                    thread.join()

                # Make sure nobody modify the pools and update them by removing
                # the references to the dead threads.
                with all_threads.locked():
                    for p in pools:
                        all_threads[p] = [t for t in all_threads[p]
                                          if t.is_alive()]

                # Start over till no thread remain in the pool in wait.

            return perform(*args, **kwargs)
    else:
        def wrapper(*args, **kwargs):

            obj = args[0]
            all_threads = obj.root_task.threads
            while True:
                # Get all the threads we should be waiting upon.
                threads = chain.from_iterable([all_threads[p]
                                               for p in all_threads])

                # If there is None break. Use any as threads is an iterator.
                if not any(threads):
                    break

                # Else join them.
                for thread in threads:
                    thread.join()

                # Make sure nobody modify the pools and update them by removing
                # the references to the dead threads.
                with all_threads.locked():
                    for p in all_threads:
                        all_threads[p] = [t for t in all_threads[p]
                                          if t.is_alive()]
            return perform(*args, **kwargs)

    wrapper.__name__ = perform.__name__
    wrapper.__doc__ = perform.__doc__

    return wrapper
