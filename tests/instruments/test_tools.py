# -*- coding: utf-8 -*-
#==============================================================================
# module : test_tools.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from hqc_meas.instruments.drivers.driver_tools import (BaseInstrument,
                                                       instrument_property,
                                                       InstrIOError,
                                                       secure_communication)
from nose.tools import assert_is_instance, assert_equal, raises

from ..util import complete_line


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


def test_instr_property_initialisation1():
    # Test initialising a read only property.
    def dummy_getter(self, val):
        pass

    p = instrument_property(dummy_getter)
    assert_equal(p.name, 'dummy_getter')


def test_instr_property_initialisation2():
    # Test initialising a write only property.
    def dummy_setter(self, val):
        pass

    p = instrument_property(fset=dummy_setter)
    assert_equal(p.name, 'dummy_setter')


@raises(ValueError)
def test_instr_property_initialisation3():
    instrument_property()


class Instr(BaseInstrument):

    caching_permissions = {'value1': True}

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        super(Instr, self).__init__(connection_info, caching_allowed,
                                    caching_permissions, auto_open)

        self._value1 = 1
        self._value2 = 2
        self.counter = 0

    @instrument_property
    def value1(self):
        return self._value1

    @value1.setter
    def value1(self, value):
        self._value1 = value

    @instrument_property
    def value2(self):
        return self._value2

    @value2.setter
    def value2(self, value):
        self._value2 = value

    @secure_communication(2)
    def error_generating_method(self):
        raise InstrIOError
        

    def open_connection(self):
        pass

    def close_connection(self):
        pass

    def reopen_connection(self):
        self.counter += 1

    def check_connection(self):
        return True

    def connected(self):
        return True


def test_instr_init1():
    """ Test that initialisation goes as expected with no optional kw.

    """
    a = Instr({})
    assert_equal(a._cache, {})
    assert_equal(a._caching_permissions, set(['value1']))


def test_instr_init2():
    """ Test init when caching is disallowed.

    """
    a = Instr({}, False)
    assert_equal(a._cache, {})
    assert_equal(a._caching_permissions, set())


def test_instr_init3():
    """ Test init when a caching permission is added.

    """
    a = Instr({}, caching_permissions={'value2': True})
    assert_equal(a._cache, {})
    assert_equal(a._caching_permissions, set(['value1', 'value2']))
    # Assert class values are unchanged.
    assert_equal(a.caching_permissions, {'value1': True})


def test_instr_init4():
    """ Test init when a caching permission is removed.

    """
    a = Instr({}, caching_permissions={'value1': False})
    assert_equal(a._cache, {})
    assert_equal(a._caching_permissions, set([]))


def test_instr_prop_get1():
    """ Test getting an instrument property from the class.

    """
    a = Instr({})
    prop = type(a).value1
    assert_is_instance(prop, instrument_property)
    assert_equal(prop.name, 'value1')


def test_instr_prop_get2():
    """ Test getting a not cached property.

    """
    a = Instr({})
    assert_equal(a.value2, 2)
    assert_equal(a._cache, {})
    a._cache['value2'] = 5
    assert_equal(a.value2, 2)


def test_instr_prop_get3():
    """ Test getting a cached property.

    """
    a = Instr({})
    assert_equal(a.value1, 1)
    assert_equal(a._cache, {'value1': 1})
    a._cache['value1'] = 5
    assert_equal(a.value1, 5)


def test_instr_prop_set1():
    """ Test setting a not cached property.

    """
    a = Instr({})
    a.value2 = 5
    assert_equal(a._value2, 5)
    assert_equal(a._cache, {})


def test_instr_prop_set2():
    """ Test setting a cached property.

    """
    a = Instr({})
    a.value1 = 5
    assert_equal(a._value1, 5)
    assert_equal(a._cache, {'value1': 5})
    # Check that the setting is skipped whe the value does not change
    #(check in coverage).
    a.value1 = 5


def test_no_cache_interferences():
    """ Test that two different instances have two different caches.

    """
    a = Instr({})
    b = Instr({})
    a.value1 = 5
    assert_equal(a._cache, {'value1': 5})
    assert_equal(b._cache, {})


def test_clear_instrument_cache1():
    """ Test clearing all the instrument cache.

    """
    a = Instr({})
    a.value1 = 5
    assert_equal(a._cache, {'value1': 5})
    a.clear_cache()
    assert_equal(a._cache, {})


def test_clear_instrument_cache2():
    """ Test clearing a part of the instrument cache.

    """
    a = Instr({}, caching_permissions={'value2': True})
    a.value1 = 5
    a.value2 = 6
    assert_equal(a._cache, {'value1': 5, 'value2': 6})
    a.clear_cache(['value2'])
    assert_equal(a._cache, {'value1': 5})


def test_check_instrument_cache1():
    """ Test getting directly the instrument cache.

    """
    a = Instr({}, caching_permissions={'value2': True})
    a.value1 = 5
    a.value2 = 6
    assert_equal(a._cache, {'value1': 5, 'value2': 6})
    assert_equal(a.check_cache(), {'value1': 5, 'value2': 6})


def test_check_instrument_cache2():
    """ Test getting directly the instrument cache.

    """
    a = Instr({}, caching_permissions={'value2': True})
    a.value1 = 5
    a.value2 = 6
    assert_equal(a._cache, {'value1': 5, 'value2': 6})
    assert_equal(a.check_cache(['value1']), {'value1': 5})


def test_secure_communication1():
    # Test securing a communication
    i = Instr({})
    try:
        i.error_generating_method()
    except InstrIOError:
        assert_equal(i.counter, 2)
        return
    raise Exception('error_generating_method did not raise the InstrIOError')


@raises(NotImplementedError)
def test_base_instrument_errors1():
    i = BaseInstrument({})
    i.open_connection()


@raises(NotImplementedError)
def test_base_instrument_errors2():
    i = BaseInstrument({})
    i.close_connection()


@raises(NotImplementedError)
def test_base_instrument_errors3():
    i = BaseInstrument({})
    i.reopen_connection()


@raises(NotImplementedError)
def test_base_instrument_errors4():
    i = BaseInstrument({})
    i.check_connection()


@raises(NotImplementedError)
def test_base_instrument_errors5():
    i = BaseInstrument({})
    i.connected()
