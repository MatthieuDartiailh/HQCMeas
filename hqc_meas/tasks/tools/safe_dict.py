# -*- coding: utf-8 -*-
# =============================================================================
# module : safe_dict.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import Atom, Dict, Value
from contextlib import contextmanager
from collections import defaultdict
from threading import RLock

class SafeDict(Atom):
    """ Dict wrapper using a lock to protect access to its values.

    Parameters
    ----------
    default : callable, optional
        Callable to use as argument for defaultdict, if unspecified a regular
        dict is used.

    """

    # --- Public API ----------------------------------------------------------

    def __init__(self, default = None):
        if default is not None:
            self._dict = defaultdict(default)

    @contextmanager
    def safe_access(self, key):
        """ Context manager to safely manipulate a value of the dict.

        """

        lock = self.lock
        lock.acquire()

        yield self._dict.get(key)

        lock.release()

    @contextmanager
    def locked(self):
        """ Freeze the dict by acquiring the instance lock.

        """
        self._lock.acquire()

        yield

        self._lock.release()

    # --- Private API ---------------------------------------------------------

    _dict = Dict()

    _lock = Value()

    def __getitem__(self, key):

        lock = self.lock
        lock.acquire()

        aux = self._dict.get(key)

        lock.release()

        return aux

    def __setitem__(self, key, value):

        lock = self.lock
        lock.acquire()

        self._dict[key] = value

        lock.release()

    def __delitem__(self, key):

        lock = self.lock
        lock.acquire()

        del self._dict[key]

        lock.release()

    def __contains__(self, key):
        return key in self._dict

    def __len__(self):
        return len(self._dict)

    def _default__lock(self):
        return RLock()
