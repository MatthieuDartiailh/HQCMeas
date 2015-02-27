# -*- coding: utf-8 -*-
# =============================================================================
# module : instr_helper.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from types import MethodType
from hqc_meas.instruments.driver_tools import BaseInstrument


class HelperMeta(type):
    """ Metaclass to make InstrHelper looks like a subclass of BaseInstrument.

    """

    def mro(cls):
        return (cls, object, BaseInstrument)


class InstrHelper(object):
    """ False driver used for testing purposes.

    Parameters
    ----------
    attrs : dict(str, list)
        Dict detailing the answers to returning when an attr is got as a list.

    callables : dict
        Dict detailing the answer to method calls either as callables or as
        list.

    """
    __metaclass__ = HelperMeta

    def __init__(self, (attrs, callables)):
        _attrs = {}
        for entry, val in attrs.items():
            if isinstance(val, list):
                # Storing value in reverse order to use pop on retrieving.
                _attrs[entry] = val[::-1]
            else:
                _attrs[entry] = val
        object.__setattr__(self, '_attrs', _attrs)

        # Dynamical method binding to instance.
        for entry, call in callables.iteritems():
            if callable(call):
                call.__name__ = entry
                object.__setattr__(self, entry, MethodType(call, self))
            else:
                call_meth = lambda *args, **kwargs: call[::-1].pop()
                call_meth.__name__ = entry
                object.__setattr__(self, entry, MethodType(call_meth, self))

    def __getattr__(self, name):
        _attrs = self._attrs
        if name in _attrs:
            if isinstance(_attrs[name], list):
                attr = _attrs[name].pop()
            else:
                attr = _attrs[name]
            if isinstance(attr, Exception):
                raise attr
            else:
                return attr

        else:
            raise AttributeError('{} has no attr {}'.format(self, name))

    def __setattr__(self, name, value):
        _attrs = self._attrs
        if name in _attrs:
            if isinstance(_attrs[name], list):
                _attrs[name].insert(0, value)
            else:
                _attrs[name] = value

        else:
            raise AttributeError('{} has no attr {}'.format(self, name))

    def close_connection(self):
        """
        """
        pass