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
    InstrIOError : General exception for instrument communication error
    BaseInstrument : Base class for all drivers
    VisaINstrument : Base class for drivers using the VISA protocol
    instrument_properties : subclass of property allowing to cache a property
        on certain condition, and to reset the cache
    secure_communication : decorator making sure that a communication error
        cannot simply be resolved by attempting again to send a message

    BypassDescriptor : Class allowing to acces to a descriptor instance
    AllowBypassableDescriptors : Metaclass for using bypassable descriptors

"""
from textwrap import fill
from inspect import cleandoc
import inspect
from visa import Instrument, VisaIOError

class InstrIOError(Exception):
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
        for name, value in members.iteritems():
            if isinstance(value, instrument_property):
                new_members['_' + name] = BypassDescriptor(value)
        members.update(new_members)
        return type.__new__(mcs, name, bases, members)

class instrument_property(property):
    """Property allowing to cache the result of a get operation and return it on
    the next get. The cache can be cleared.

    """
    _cache = None
    _allow_caching = False

    def __get__(self, obj, objtype = None):
        """
        """
        if self._cache is not None:
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

    def set_caching_authorization(self, author):
        """Allow or disallow to cache the property.
        """
        self._allow_caching = author

def secure_communication(method, max_iter = 10):
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

    if method:
        # This was an actual decorator call, ex: @secure_communication
        return decorator(method)
    else:
        # This is a factory call, ex: @secure_communication()
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
                 caching_permissions = {}):
        super(BaseInstrument, self).__init__()
        if caching_allowed:
            self.caching_permissions.update(caching_permissions)
            for prop_name in self.caching_permissions:
                #Accessing bypass descriptor to call their methods
                prop = getattr(self, '_' + prop_name)
                author  = self.caching_permissions[prop_name]
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

    def clear_instrument_cache(self, properties = None):
        """Clear the cache of all the properties or only the one of specified
        ones

        Parameters
        ----------
        properties : iterable of str, optionnal
            Name of the properties whose cache should be cleared. All caches
            will be cleared if not specified.
        """
        test = lambda obj: isinstance(obj, instrument_property)
        if properties is not None:
            for name, instr_prop in inspect.getmembers(self.__class__, test):
                if name.startswith('_'):
                    # Calling method only on bypassed descriptor
                    instr_prop.clear_cache()
        else:
            for name, instr_prop in inspect.getmembers(self.__class__, test):
                if name.startswith('_') and name[1:] in properties:
                    # Calling method only on bypassed descriptor
                    instr_prop.clear_cache()

class VisaInstrument(BaseInstrument):
    """Base class for drivers using the VISA library to communicate

    This class uses the PyVisa binder to the VISA library to open a
    communication. The PyVisa object (Instrument instance) is cached and this
    class provides conveninence methods to call all its method and propeties
    to set its attributes. The connection to the instrument is opened upon
    initialisation.

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
    connection_str : VISA string uses to open the communication

    The following attributes simply reflects the attribute of a `PyVisa`
    `Instrument` object :
    time_out
    send_end
    term_chars
    delay
    values_format
    chunk_size

    Methods
    -------
    open_connection() :
        Open the connection to the instrument using the `connection_str`
    close_connection() :
        Close the connection with the instrument
    reopen_connection() :
        Reopen the connection with the instrument with the same parameters as
        previously
    check_connection() : virtual
        Check whether or not the cache is likely to have been corrupted

    The following method simply call the PyVisa method of the driver
    write(mess)
    read()
    read_values()
    ask(mess)
    ask_for_values()
    clear()
    trigger()
    read_raw()

    """
    secure_com_except = (InstrIOError, VisaIOError)

    def __init__(self, connection_info, caching_allowed = True,
                 caching_permissions = {}):
        super(VisaInstrument, self).__init__(caching_allowed,
                                                caching_permissions)
        if connection_info['additionnal_mode'] != '':
            self.connection_str = connection_info['connection_type']\
                                + '::' + connection_info['address']\
                                + '::' + connection_info['additionnal_mode']
        else:
            self.connection_str = connection_info['connection_type']\
                                + '::' + connection_info['address']
        self._driver = None
        self.open_connection()

    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`
        """
        try:
            self._driver = Instrument(self.connection_str, **para)
        except VisaIOError as er:
            raise InstrIOError(str(er))

    def close_connection(self):
        """Close the connection to the instr
        """
        if self._driver:
            self._driver.close()
        self._driver = None
        return True

    def reopen_connection(self):
        """Reopen the connection with the instrument with the same parameters as
        previously
        """
        para = {'timeout' : self._driver.timeout,
                'send_end' : self._driver.send_end,
                'delay' : self._driver.delay,
                'term_chars' : self._driver.term_chars,
                'values_format' : self._driver.values_format,
                'chunk_size' : self._driver.chunk_size,
                }
        self._driver.close()
        self.open_connection(**para)

    def write(self, message):
        """Send the specified message to the instrument.

        Simply call the `write` method of the `Instrument` object stored in
        the attribute `_driver`
        """
        self._driver.write(message)

    def read(self):
        """Read one line of the instrument's buffer.

        Simply call the `read` method of the `Instrument` object stored in
        the attribute `_driver`
        """
        return self._driver.read()

    def read_values(self, format = None):
        """Read one line of the instrument's buffer and convert to values.

        Simply call the `read_values` method of the `Instrument` object
        stored in the attribute `_driver`
        """
        return self._driver.read_values(format = format)

    def ask(self, message):
        """Send the specified message to the instrument and read its answer.

        Simply call the `ask` method of the `Instrument` object stored in
        the attribute `_driver`
        """
        return self._driver.ask(message)

    def ask_for_values(self, message, format = None):
        """Send the specified message to the instrument and convert its answer
        to values.

        Simply call the `ask_for_values` method of the `Instrument` object
        stored in the attribute `_driver`
        """
        return self._driver.ask_for_values(message, format)

    def clear(self):
        """Resets the device (highly bus dependent).

        Simply call the `clear` method of the `Instrument` object stored in
        the attribute `_driver`
        """
        return self._driver.clear()

    def trigger(self):
        """Send a trigger to the instrument.

        Simply call the `trigger` method of the `Instrument` object stored
        in the attribute `_driver`
        """
        return self._driver.trigger()

    def read_raw(self):
        """Read one line of the instrument buffer and return without stripping
        termination caracters.

        Simply call the `read_raw` method of the `Instrument` object stored
        in the attribute `_driver`
        """
        return self._driver.read_raw()

    def _timeout(self):
        return self._driver.timeout

    def _set_timeout(self, value):
        self._driver.timeout = value

    timeout = property(_timeout, _set_timeout)
    """Conveninence to set/get the `timeout` attribute of the `Instrument`
    object"""

    def _term_chars(self):
        return self._driver.term_chars

    def _set_term_chars(self, value):
        self._driver.term_chars = value

    term_chars = property(_term_chars, _set_term_chars)
    """Conveninence to set/get the `term_chars` attribute of the `Instrument`
    object"""

    def _send_end(self):
        return self._driver.send_end

    def _set_send_end(self, value):
        self._driver.send_end = value

    send_end = property(_send_end, _set_send_end)
    """Conveninence to set/get the `send_end` attribute of the `Instrument`
    object"""

    def _delay(self):
        return self._driver.delay

    def _set_delay(self, value):
        self._driver.delay = value

    delay = property(_delay, _set_delay)
    """Conveninence to set/get the `delay` attribute of the `Instrument`
    object"""

    def _values_format(self):
        return self._driver.values_format

    def _set_values_format(self, value):
        self._driver.values_format = value

    values_format = property(_values_format, _set_values_format)
    """Conveninence to set/get the `values_format` attribute of the `Instrument`
    object"""

    def _chunk_size(self):
        return self._driver.chunk_size

    def _set_chunk_size(self, value):
        self._driver.chunk_size = value

    chunk_size = property(_chunk_size, _set_chunk_size)
    """Conveninence to set/get the `chunk_size` attribute of the `Instrument`
    object"""