# -*- coding: utf-8 -*-
#==============================================================================
# module : instr_helper.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================


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
    def __init__(self, attrs, callables):
        self._attrs = {}
        for entry in attrs:
            self._attrs[entry] = attrs[entry][::-1]

        self._callables = {}
        for entry, call in callables.iteritems():
            if callable(call):
                self._callables[entry] = call
            else:
                self._callables[entry] = call[::-1]

    def __getattr__(self, name):
        if name in self._attrs:
            attr = self._attrs[name].pop()
            if isinstance(attr, Exception):
                raise attr
            else:
                return attr

        elif name in self._methods:
            call = self._methods[name]
            if callable(call):
                return call
            else:
                return lambda *args, **kwargs: call.pop()
