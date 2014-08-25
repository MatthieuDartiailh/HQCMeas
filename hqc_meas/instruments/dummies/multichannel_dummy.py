# -*- coding: utf-8 -*-
from ..driver_tools import (InstrIOError, instrument_property,
                            secure_communication)
from ..dummy import DummyInstrument


class DummyChannel(DummyInstrument):
    """

    """
    def __init__(self, dummy, channel_num, caching_allowed=True,
                 caching_permissions={}):
        super(DummyChannel, self).__init__(None, caching_allowed,
                                           caching_permissions)
        self._dummy = dummy
        self._channel = channel_num
        self._float = 0.0
        self._int = 0
        self._enum = ['ON', 'OFF']
        self._enum_val = 'OFF'

    @instrument_property
    def dummy_float(self):
        if self.fail:
            raise InstrIOError('Failed to get dummy_float')
        return self._float

    @dummy_float.setter
    def dummy_float(self, val):
        if self.fail or type(val) != float:
            raise InstrIOError('Wrong val for dummy_float')
        print 'dummy_float :', val
        self._float = val

    @instrument_property
    def dummy_int(self):
        if self.fail:
            raise InstrIOError('Failed to get dummy_int')
        return self._int

    @dummy_int.setter
    def dummy_int(self, val):
        if self.fail or type(val) != int:
            raise InstrIOError('Wrong val for dummy_int')
        print 'dummy_int :', val
        self._int = val

    @instrument_property
    def dummy_enum(self):
        if self.fail:
            raise InstrIOError('Failed to get dummy_enum')
        return self._enum_val

    @dummy_enum.setter
    def dummy_enum(self, val):
        if self.fail or val not in self._enum:
            raise InstrIOError('Wrong val for dummy_enum')
        print 'dummy_enum :', val
        self._enum_val = val

    @secure_communication()
    def dummy_method(self, arg1, arg2=None):
        return arg1, arg2


class MultichannelDummy(DummyInstrument):
    """
    """
    def __init__(self,  connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super(MultichannelDummy, self).__init__(connection_info,
                                                caching_allowed,
                                                caching_permissions,
                                                auto_open)
        self._float = 0.0

    def get_channel(self, channel_id):
        """
        """
        return DummyChannel(self, channel_id)

    @secure_communication()
    def dummy_method(self, arg1, arg2=None):
        return arg1, arg2

    @instrument_property
    def dummy_float(self):
        if self.fail:
            raise InstrIOError('Failed to get dummy_float')
        return self._float

    @dummy_float.setter
    def dummy_float(self, val):
        if self.fail or type(val) != float:
            raise InstrIOError('Wrong val for dummy_float')
        print 'dummy_float :', val
        self._float = val

DRIVERS = {'MultichannelDummy': MultichannelDummy}
