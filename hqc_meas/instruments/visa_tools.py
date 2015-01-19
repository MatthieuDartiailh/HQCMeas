# -*- coding: utf-8 -*-
# TODO this is compatible with PyVisa 1.5 but does not use the new recommended
# API
try:
    from pyvisa.visa import Instrument, VisaIOError, VisaTypeError
except Exception:
    from pyvisa.legacy.visa import Instrument, VisaIOError
    from pyvisa.errors import VisaTypeError

from .driver_tools import BaseInstrument, InstrIOError


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

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super(VisaInstrument, self).__init__(connection_info, caching_allowed,
                                             caching_permissions)
        if connection_info['additionnal_mode'] != '':
            self.connection_str =\
                str(connection_info['connection_type']
                    + '::' + connection_info['address']
                    + '::' + connection_info['additionnal_mode'])
        else:
            self.connection_str =\
                str(connection_info['connection_type']
                    + '::' + connection_info['address'])
        self._driver = None
        if auto_open:
            self.open_connection()

    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`
        """
        try:
            self._driver = Instrument(self.connection_str, **para)
        except VisaIOError as er:
            self._driver = None
            raise InstrIOError(str(er))

    def close_connection(self):
        """Close the connection to the instr
        """
        if self._driver:
            self._driver.close()
        self._driver = None
        return True

    def reopen_connection(self):
        """Reopen the connection with the instrument with the same parameters
        as previously.

        """
        para = {'timeout': self._driver.timeout,
                'send_end': self._driver.send_end,
                'delay': self._driver.delay,
                'term_chars': self._driver.term_chars,
                'values_format': self._driver.values_format,
                'chunk_size': self._driver.chunk_size,
                }
        self._driver.close()
        self.open_connection(**para)

    def connected(self):
        """Returns whether commands can be sent to the instrument
        """
        return bool(self._driver)

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

    def read_values(self, format=None):
        """Read one line of the instrument's buffer and convert to values.

        Simply call the `read_values` method of the `Instrument` object
        stored in the attribute `_driver`
        """
        return self._driver.read_values(format=format)

    def ask(self, message):
        """Send the specified message to the instrument and read its answer.

        Simply call the `ask` method of the `Instrument` object stored in
        the attribute `_driver`
        """
        return self._driver.ask(message)

    def ask_for_values(self, message, format=None):
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
    """Conveninence to set/get the `values_format` attribute of the
    `Instrument` object"""

    def _chunk_size(self):
        return self._driver.chunk_size

    def _set_chunk_size(self, value):
        self._driver.chunk_size = value

    chunk_size = property(_chunk_size, _set_chunk_size)
    """Conveninence to set/get the `chunk_size` attribute of the `Instrument`
    object"""

DRIVER_PACKAGES = ['visa']
DRIVER_TYPES = {'Visa': VisaInstrument}
