# -*- coding: utf-8 -*-

from .driver_tools import BaseInstrument, InstrIOError
import random
random.seed()


class DummyInstrument(BaseInstrument):
    """
    """
    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        self.fail = random.randint(0, 1)
        self.corrupted = False
        self._connected = False
        super(DummyInstrument, self).__init__(connection_info, caching_allowed,
                                              caching_permissions, auto_open)

    def open_connection(self):
        if self.fail:
            raise InstrIOError('Failed to open connection')
        self._connected = True

    def close_connection(self):
        if self.fail:
            raise InstrIOError('Failed to close connection')
        self._connected = False

    def reopen_connection(self):
        if self.fail:
            raise InstrIOError('Failed to reopen connection')

    def check_connection(self):
        return self.corrupted

    def connected(self):
        """Return whether or not commands can be sent to the instrument.

        """
        return self._connected

DRIVER_TYPES = {'Dummy': DummyInstrument}
DRIVER_PACKAGES = ['dummies']
