# -*- coding: utf-8 -*-
#==============================================================================
# module : walks.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from collections import defaultdict


def flatten_walk(walk, entries):
    """ Convert a nested list in a flat dict by gathering entries in sets.

    Parameters
    ----------
    walk : list
        The nested list returned by the walk method of the root task.

    entries : list(str)
        The list of entries to look for in the walk.

    Returns
    -------
    results : dict(str: set)
        Dict containing the values of the entries as sets. This dict can then
        be used to gather function and or classes needed at runtime.

    """
    results = defaultdict(set)
    for step in walk:
        if isinstance(step, list):
            aux = flatten_walk(step, entries)
            for key in aux:
                results[key].update(aux[key])
        else:
            for entry in entries:
                if entry in step and step[entry] is not None:
                    results[entry].add(step[entry])

    return results
