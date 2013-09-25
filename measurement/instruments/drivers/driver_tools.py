from textwrap import fill
from inspect import cleandoc
import inspect
from visa import Instrument, VisaIOError

class InstrIOError(Exception):
    """
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
    def __new__(cls, name, bases, members):
        new_members = {}
        for name, value in members.iteritems():
            if isinstance(value, instrument_property):
                new_members['_' + name] = BypassDescriptor(value)
        members.update(new_members)
        return type.__new__(cls, name, bases, members)

class instrument_property(property):
    """
    """
    _cache = None
    _allow_caching = False

    def __get__(self, obj, objtype = None):
        """
        """
        if self._cache is not None:
            return self._cache
        else:
          return super(instrument_property,self).__get__(obj, objtype)

    def __set__(self, obj, value):
        """
        """
        super(instrument_property,self).__set__(obj, value)
        if self._allow_caching:
            self._cache = value

    def clear_cache(self):
        """
        """
        self._cache = None

    def set_caching_authorization(self, author):
        """
        """
        self._allow_caching = author

def secure_communication(method, max_iter = 10):
    """
    """
    def decorator(method):
        """
        """
        def wrapper(self, *args, **kwargs):

            i = 0
            while i < max_iter:
                try:
                    return method(self, *args, **kwargs)
                    break
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
        # This was an actual decorator call, ex: @cached_property
        return decorator(method)
    else:
        # This is a factory call, ex: @cached_property()
        return decorator

class BaseInstrument(object):
    """
    """
    __metaclass__ = AllowBypassableDescriptors
    caching_permissions = {}
    secure_com_except = ()

    def __init__(self, caching_allowed = True, caching_permissions = {}):
        super(BaseInstrument, self).__init__()
        if caching_allowed:
            self.caching_permissions.update(caching_permissions)
            for prop_name in self.caching_permissions:
                #Accessing bypass descriptor to call their methods
                prop = getattr(self, '_' + prop_name)
                author  = self.caching_permissions[prop_name]
                prop.set_caching_authorization(author)

    def open_connection(self):
        """
        """
        message = fill(cleandoc(
                    '''This method is used to open the connectionwith the
                    instrument and should be implemented by classes
                    subclassing BaseInstrument'''),
                    80)
        raise NotImplementedError(message)

    def close_connection(self):
        """
        """
        message = fill(cleandoc(
                    '''This method is used to close the connection with the
                    instrument and should be implemented by classes
                    subclassing BaseInstrument'''),
                    80)
        raise NotImplementedError(message)

    def reopen_connection(self):
        """
        """
        message = fill(cleandoc(
                    '''This method is used to reopen a connection whose state
                    is suspect, for example the last message sent did not
                    go through.'''),
                    80)
        raise NotImplementedError(message)

    def check_connection(self):
        """
        """
        message = fill(cleandoc(
                        '''This method is used to check that the instrument is
                        in remote mode and that none of the values in the cache
                        has been corrupted by a local user.'''),
                    80)
        raise NotImplementedError(message)

    def clear_instrument_cache(self):
        """
        """
        test = lambda obj: isinstance(obj, instrument_property)
        for name, instr_prop in inspect.getmembers(self.__class__, test):
            if name.startswith('_'):
                # Calling method only on bypassed descriptor
                instr_prop.clear_cache()

class VisaInstrument(BaseInstrument):
    """
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

        self.open_connection()

    def open_connection(self, **para):
        """
        """
        try:
            self._driver = Instrument(self.connection_str, **para)
        except VisaIOError as er:
            raise InstrIOError(str(er))

    def close_connection(self):
        """
        """
        self._driver.close()
        return True

    def reopen_connection(self):
        """
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

    def check_connection(self):
        """
        """
        pass

    def write(self, message):
        """
        """
        self._driver.write(message)

    def read(self):
        """
        """
        return self._driver.read()

    def read_values(self, format = None):
        """
        """
        return self._driver.read(format)

    def ask(self, message):
        """
        """
        return self._driver.ask(message)

    def ask_for_values(self, message, format = None):
        """
        """
        return self._driver.ask_for_values(message, format)

    def clear(self):
        """
        """
        return self._driver.clear()

    def trigger(self):
        """
        """
        return self._driver.trigger()

    def read_raw(self):
        """
        """
        return self._driver.read_raw()

    def _timeout(self):
        """
        """
        return self._driver.timeout

    def _set_timeout(self, value):
        """
        """
        self._driver.timeout = value

    timeout = property(_timeout,_set_timeout)

    def _term_chars(self):
        """
        """
        return self._driver.term_chars

    def _set_term_chars(self, value):
        self._driver.term_chars = value

    term_chars = property(_term_chars, _set_term_chars)

    def _send_end(self):
        """
        """
        return self._driver.send_end

    def _set_send_end(self, value):
        self._driver.send_end = value

    send_end = property(_send_end, _set_send_end)

    def _delay(self):
        """
        """
        return self._driver.delay

    def _set_delay(self, value):
        self._driver.delay = value

    delay = property(_delay, _set_delay)

    def _values_format(self):
        """
        """
        return self._driver.values_format

    def _set_values_format(self, value):
        self._driver.values_format = value

    values_format = property(_values_format, _set_values_format)

    def _chunk_size(self):
        return self._driver.chunk_size

    def _set_chunk_size(self, value):
        self._driver.chunk_size = value

    chunk_size = property(_chunk_size, _set_chunk_size)