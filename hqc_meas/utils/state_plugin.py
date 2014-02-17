# -*- coding: utf-8 -*-

class State(Declarative):
    """
    """
    # Will be used to dynamically create an atom class with value members,
    # and observe plugin to update state object in consequence
    values = d_(List(Str()))