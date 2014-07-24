# -*- coding: utf-8 -*-
# =============================================================================
# module : safe_dict.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import Atom, Instance, Value, Int
from contextlib import contextmanager
from collections import defaultdict
from threading import RLock, Lock


class SharedCounter(Atom):
    """ Thread-safe counter object.

    """

    # --- Public API ----------------------------------------------------------

    #: Current count of the counter. User should not manipulate this directly.
    count = Int()

    def increment(self):
        """

        """
        self._lock.acquire()
        self.count += 1
        self._lock.release()

    def decrement(self):
        """

        """
        self._lock.acquire()
        self.count += -1
        self._lock.release()

    # --- Private API ---------------------------------------------------------

    _lock = Value()

    def _default__lock(self):
        return Lock()


class SharedDict(Atom):
    """ Dict wrapper using a lock to protect access to its values.

    Parameters
    ----------
    default : callable, optional
        Callable to use as argument for defaultdict, if unspecified a regular
        dict is used.

    """

    # --- Public API ----------------------------------------------------------

    def __init__(self, default=None):
        super(SharedDict, self).__init__()
        if default is not None:
            self._dict = defaultdict(default)
        else:
            self._dict = {}

    @contextmanager
    def safe_access(self, key):
        """ Context manager to safely manipulate a value of the dict.

        """
        lock = self._lock
        lock.acquire()

        yield self._dict[key]

        lock.release()

    @contextmanager
    def locked(self):
        """ Freeze the dict by acquiring the instance lock.

        """
        self._lock.acquire()

        yield

        self._lock.release()

    def get(self, key, default=None):
        self._lock.acquire()

        aux = self._dict.get(key, default)

        self._lock.release()

        return aux

    # --- Private API ---------------------------------------------------------

    _dict = Instance((dict, defaultdict))

    _lock = Value()

    def __getitem__(self, key):

        lock = self._lock
        lock.acquire()

        aux = self._dict[key]

        lock.release()

        return aux

    def __setitem__(self, key, value):

        lock = self._lock
        lock.acquire()

        self._dict[key] = value

        lock.release()

    def __delitem__(self, key):

        lock = self._lock
        lock.acquire()

        del self._dict[key]

        lock.release()

    def __contains__(self, key):
        return key in self._dict

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)

    def _default__lock(self):
        return RLock()
