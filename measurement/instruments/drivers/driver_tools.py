from textwrap import fill
from visa import Instrument

class InstrIOError(Exception):
    """
    """
    pass

class instrument_property(property):
    """
    """
    _cache = None
    allow_caching = False

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
        super(instrument_property,self).__get__(obj, value)
        if self.allow_caching:
            self._cache = value

    def clear_cache(self):
        """
        """
        self._cache = None

class BaseInstrument(object):
    """
    """
    caching_permissions = {}
    secure_com_except = ()

    def __init__(self, caching_switch = False, caching_permissions = {}):
        super(BaseInstrument, self).__init__()
        if not caching_switch:
            self.caching_permissions.update(caching_permissions)
            for prop_name in self.caching_permissions:
                prop = getattr(self, prop_name)
                prop.allow_caching = self.caching_permissions[prop_name]

    def open_connection(self):
        """
        """
        message = fill('''This method is used to open the connection with the
                       instrument and should be implemented by classes
                       subclassing BaseInstrument''', 80)
        raise NotImplementedError(message)

    def close_connection(self):
        """
        """
        message = fill('''This method is used to close the connection with the
                       instrument and should be implemented by classes
                       subclassing BaseInstrument''', 80)
        raise NotImplementedError(message)

    def reopen_connection(self):
        """
        """
        message = fill('''This method is used to reopen a connection whose state
                       is suspect, for example the last message sent did not
                       go through.''', 80)
        raise NotImplementedError(message)

    def check_connection(self):
        """
        """
        message = fill('''This method is used to check that the instrument is
                       in remote mode and that none of the values in the cache
                       has been corrupted by a local user.''', 80)
        raise NotImplementedError(message)

    def secure_communication(self, max_iter = 10):
        """
        """
        def decorator(method):
            """
            """
            def wrapper(*args, **kwargs):
                wrapper.__name__ = method.__name__
                wrapper.__doc__ = method.__doc__
                i = 0
                while i < max_iter:
                    try:
                        return method(*args, **kwargs)
                        break
                    except self.secure_com_except:
                        if i == max_iter-1:
                            raise
                        else:
                            self.close_connection

            return wrapper

        return decorator

class VisaInstrument(BaseInstrument):
    """
    """
    def __init__(self, connection_info, caching_switch = False,
                 caching_permissions = {}):
        super(VisaInstrument, self).__init__(caching_switch,caching_permissions)
        if connection_info['additionnal_mode'] != '':
            self.connection_str = connection_info['connection_type']\
                                + '::' + connection_info['address']\
                                + '::' + connection_info['additionnal_mode']
        else:
            self.connection_str = connection_info['connection_type']\
                                + '::' + connection_info['address']

        self.open_connection()

    def open_connection(self):
        """
        """
        self._driver = Instrument(self.connection_str)

    def close_connection(self):
        """
        """
        self._driver.close()
        return True

    def reopen_connection(self):
        """
        """
        para = {'timeout' : self._driver.timeout,
                'send_send' : self._driver.send_end,
                'delay' : self._driver.delay,
                'term_chars' : self._driver.term_chars,
                'values_format' : self._driver.values_format,
                'chunk_size' : self._driver.chunk_size,
                }
        self._driver.close()
        self._driver = Instrument(self.connection_str, **para)

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