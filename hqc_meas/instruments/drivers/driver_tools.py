#==============================================================================
# module : driver_tools.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
This module defines base tools for writing instrument drivers.

All instruments drivers must inherit from `BaseInstrument` which ensure they
can use instrument properties (see below). Drivers should not directly subclass
`BaseInstrument` but one of it subclass implementing a connection protocol
(defining a kind of driver). For the time being the only supported protocol use
the VISA library.

:Contains:
    InstrIOError :
        General exception for instrument communication error
    BaseInstrument :
        Base class for all drivers
    VisaInstrument : .
        Base class for drivers using the VISA protocol
    instrument_properties :
        subclass of property allowing to cache a property on certain condition,
        and to reset the cache
    secure_communication :
        decorator making sure that a communication error cannot simply be
        resolved by attempting again to send a message
    BypassDescriptor :
        Class allowing to acces to a descriptor instance
    AllowBypassableDescriptors :
        Metaclass for using bypassable descriptors

"""
from textwrap import fill
from inspect import cleandoc
import inspect

class InstrError(Exception):
    """Generic error raised when an instrument does not behave as expected
    """
    pass


class InstrIOError(InstrError):
    """Generic error raised when an instrument does not behave as expected
    """
    pass


class BypassDescriptor(object):
    """Class allowing to acces to a descriptor instance"""
    def __init__(self, descriptor):
        self.descriptor = descriptor

    def __getattr__(self, name):
        return getattr(self.descriptor, name)


class AllowBypassableDescriptors(type):
    """Metaclass allowing to access to bypassed descriptor (_descriptorName).
    Here customized to access instrument properties.

    """
    def __new__(mcs, name, bases, members):
        new_members = {}
        for n, value in members.iteritems():
            if isinstance(value, instrument_property):
                new_members['_' + n] = BypassDescriptor(value)
        members.update(new_members)
        return type.__new__(mcs, name, bases, members)


class instrument_property(property):
    """Property allowing to cache the result of a get operation and return it
    on the next get. The cache can be cleared.

    """
    _cache = None
    _allow_caching = False

    def __get__(self, obj, objtype = None):
        """
        """
        if self._allow_caching:
            if self._cache is None:
                self._cache = super(instrument_property, self).__get__(obj,
                                                                     objtype)
            return self._cache
        else:
           return super(instrument_property, self).__get__(obj, objtype)

    def __set__(self, obj, value):
        """
        """
        if self._allow_caching:
            if self._cache == value:
                return
            super(instrument_property, self).__set__(obj, value)
            self._cache = value
        else:
            super(instrument_property, self).__set__(obj, value)

    def clear_cache(self):
        """Clear the cached value.
        """
        self._cache = None

    def check_cache(self):
        """Return the cache value
        """
        return self._cache

    def set_caching_authorization(self, author):
        """Allow or disallow to cache the property.
        """
        self._allow_caching = author

def secure_communication(max_iter = 10):
    """Decorator making sure that a communication error cannot simply be
    resolved by attempting again to send a message.

    Parameters
    ----------
    max_iter : int, optionnal
        Maximum number of attempt to perform before propagating the exception

    """
    def decorator(method):
        def wrapper(self, *args, **kwargs):

            i = 0
            # Try at most `max_iter` times to excute method
            while i < max_iter:
                try:
                    return method(self, *args, **kwargs)
                    break
                # Catch all the exception specified by the driver
                except self.secure_com_except as e:
                    if i == max_iter-1:
                        raise
                    else:
                        print e
                        self.reopen_connection()
                        i += 1

        wrapper.__name__ = method.__name__
        wrapper.__doc__ = method.__doc__
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
    __metaclass__ = AllowBypassableDescriptors
    caching_permissions = {}
    secure_com_except = ()
    owner = ''

    def __init__(self, connection_info, caching_allowed = True,
                 caching_permissions = {}, auto_open = True):
        super(BaseInstrument, self).__init__()
        if caching_allowed:
            # Avoid overriding class attribute
            perms = self.caching_permissions.copy()
            perms.update(caching_permissions)
            for prop_name in perms:
                #Accessing bypass descriptor to call their methods
                prop = getattr(self, '_' + prop_name)
                author = perms[prop_name]
                prop.set_caching_authorization(author)

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
        """Check whether or not the cache is likely to have been corrupted
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

    def clear_instrument_cache(self, properties = None):
        """Clear the cache of all the properties or only the one of specified
        ones

        Parameters
        ----------
        properties : iterable of str, optionnal
            Name of the properties whose cache should be cleared. All caches
            will be cleared if not specified.
        """
        test = lambda obj: isinstance(obj, BypassDescriptor)
        if properties is None:
            for name, instr_prop in inspect.getmembers(self.__class__, test):
                if name.startswith('_'):
                    # Calling method only on bypassed descriptor
                    instr_prop.clear_cache()
        else:
            for name, instr_prop in inspect.getmembers(self.__class__, test):
                if name.startswith('_') and name[1:] in properties:
                    # Calling method only on bypassed descriptor
                    instr_prop.clear_cache()

    def check_instrument_cache(self, properties):
        """
        """
        test = lambda obj: isinstance(obj, BypassDescriptor)
        for name, instr_prop in inspect.getmembers(self.__class__, test):
                if name.startswith('_') and name[1:] == properties:
                    # Calling method only on bypassed descriptor
                    instr_prop.check_cache()
