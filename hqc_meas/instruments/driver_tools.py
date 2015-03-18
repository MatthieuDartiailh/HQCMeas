# -*- coding: utf-8 -*-
# =============================================================================
# module : driver_tools.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
This module defines base tools for writing instrument drivers.

All instruments drivers must inherit from `BaseInstrument` which ensure they
can use instrument properties (see below). Drivers should not directly subclass
`BaseInstrument` but one of it subclass implementing a connection protocol
(defining a kind of driver). For the time being the only supported protocol use
the VISA library.

:Contains:
    InstrError :
        General exception for instrument error.
    InstrIOError :
        General exception for instrument communication error.
    BaseInstrument :
        Base class for all drivers.
    instrument_properties :
        subclass of property allowing to cache a property on certain condition,
        and to reset the cache.
    secure_communication :
        decorator making sure that a communication error cannot simply be
        resolved by attempting again to send a message.

"""
from textwrap import fill
from inspect import cleandoc
import inspect
from functools import wraps


class InstrError(Exception):
    """Generic error raised when an instrument does not behave as expected
    """
    pass


class InstrIOError(InstrError):
    """Generic error raised when an instrument does not behave as expected
    """
    pass


class instrument_property(property):
    """Property allowing to cache the result of a get operation and return it
    on the next get. The cache can be cleared.

    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        super(instrument_property, self).__init__(fget, fset, fdel, doc)
        if fget is not None:
            self.name = fget.__name__
        elif fset is not None:
            self.name = fset.__name__
        else:
            err = 'Need either a setter or getter for an instrument_property.'
            raise ValueError(err)

        self.type = None
        self.valid_values = []

    def __get__(self, obj, objtype=None):
        """
        """
        if obj is not None:
            name = self.name
            if name in obj._caching_permissions:
                try:
                    return obj._cache[name]
                except KeyError:
                    aux = super(instrument_property, self).__get__(obj,
                                                                   objtype)
                    obj._cache[name] = aux
                    return aux
            else:
                return super(instrument_property, self).__get__(obj, objtype)

        else:
            return self

    def __set__(self, obj, value):
        """
        """
        name = self.name
        if name in obj._caching_permissions:
            try:
                if obj._cache[name] == value:
                    return
            except KeyError:
                pass
            super(instrument_property, self).__set__(obj, value)
            obj._cache[name] = value
        else:
            super(instrument_property, self).__set__(obj, value)


def secure_communication(max_iter=2):
    """Decorator making sure that a communication error cannot simply be
    resolved by attempting again to send a message.

    Parameters
    ----------
    max_iter : int, optionnal
        Maximum number of attempt to perform before propagating the exception

    """
    def decorator(method):

        @wraps(method)
        def wrapper(self, *args, **kwargs):

            i = 0
            # Try at most `max_iter` times to excute method
            while i < max_iter + 1:
                try:
                    return method(self, *args, **kwargs)

                # Catch all the exception specified by the driver
                except self.secure_com_except as e:
                    if i == max_iter:
                        raise
                    else:
                        print e
                        self.reopen_connection()
                        i += 1

        wrapper.__wrapped__ = method
        return wrapper

    return decorator


class BaseInstrument(object):
    """Base class for all drivers

    This class set up the caching mechanism and its management in terms of
    permissions and cleaning of the caches.

    Parameters
    ----------
    connection_info : dict
        Dict containing all the necessary information to open a connection to
        the instrument
    caching_allowed : bool, optionnal
        Boolean use to determine if instrument properties can be cached
    caching_permissions : dict(str : bool), optionnal
        Dict specifying which instrument properties can be cached, override the
        default parameters specified in the class attribute.

    Attributes
    ----------
    caching_permissions : dict(str : bool)
        Dict specifying which instrument properties can be cached.
    secure_com_except : tuple(Exception)
        Tuple of the exceptions to be catched by the `secure_communication`
        decorator
    owner : str
        Identifier of the last owner of the driver. Used to know whether or not
        previous settings might heve been modified by other parts of the
        program.

    Methods
    -------
    open_connection() : virtual
        Open the connection to the instrument
    close_connection() : virtual
        Close the connection with the instrument
    reopen_connection() : virtual
        Reopen the connection with the instrument with the same parameters as
        previously
    check_connection() : virtual
        Check whether or not the cache is likely to have been corrupted
    clear_cache(properties = None)
        Clear the cache of some or all instrument properties

    """
    caching_permissions = {}
    secure_com_except = (InstrIOError)
    owner = ''

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super(BaseInstrument, self).__init__()
        if caching_allowed:
            # Avoid overriding class attribute
            perms = self.caching_permissions.copy()
            perms.update(caching_permissions)
            self._caching_permissions = set([key for key in perms
                                             if perms[key]])
        else:
            self._caching_permissions = set([])
        self._cache = {}

    def open_connection(self):
        """Open a connection to an instrument
        """
        message = fill(cleandoc(
            '''This method is used to open the connection with the
            instrument and should be implemented by classes
            subclassing BaseInstrument'''),
            80)
        raise NotImplementedError(message)

    def close_connection(self):
        """Close the connection established previously using `open_connection`
        """
        message = fill(cleandoc(
            '''This method is used to close the connection with the
            instrument and should be implemented by classes
            subclassing BaseInstrument'''),
            80)
        raise NotImplementedError(message)

    def reopen_connection(self):
        """Reopen the connection established previously using `open_connection`
        """
        message = fill(cleandoc(
            '''This method is used to reopen a connection whose state
            is suspect, for example the last message sent did not
            go through.'''),
            80)
        raise NotImplementedError(message)

    def check_connection(self):
        """Check whether or not the cache is likely to have been corrupted.

        """
        message = fill(cleandoc(
            '''This method is used to check that the instrument is
            in remote mode and that none of the values in the cache
            has been corrupted by a local user.'''),
            80)
        raise NotImplementedError(message)

    def connected(self):
        """Return whether or not commands can be sent to the instrument
        """
        message = fill(cleandoc(
            '''This method returns whether or not command can be
            sent to the instrument'''),
            80)
        raise NotImplementedError(message)

    def clear_cache(self, properties=None):
        """ Clear the cache of all the properties or only the one of specified
        ones.

        Parameters
        ----------
        properties : iterable of str, optionnal
            Name of the properties whose cache should be cleared. All caches
            will be cleared if not specified.

        """
        test = lambda obj: isinstance(obj, instrument_property)
        cache = self._cache
        if properties:
            for name, instr_prop in inspect.getmembers(self.__class__, test):
                if name in properties and name in cache:
                    del cache[name]
        else:
            self._cache = {}

    def check_cache(self, properties=None):
        """Return the value of the cache of the instruments

        Parameters
        ----------
        properties : iterable of str, optionnal
            Name of the properties whose cache should be cleared. All caches
            will be cleared if not specified.

        Returns
        -------
        cache : dict
            Dict containing the cached value, if the properties arg is given
            None will be returned for the field with no cached value.

        """
        test = lambda obj: isinstance(obj, instrument_property)
        cache = {}
        if properties:
            for name, instr_prop in inspect.getmembers(self.__class__, test):
                if name in properties:
                    cache[name] = self._cache.get(name)
        else:
            cache = self._cache.copy()

        return cache
