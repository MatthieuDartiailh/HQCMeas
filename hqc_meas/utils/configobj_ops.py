# -*- coding: utf-8 -*-
#==============================================================================
# module : config_obj_operations.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from configobj import Section


def include_configobj(new_parent, config):
    """ Make a ConfigObj part of another one and preserves the depth.

    This function will copy all entries from config.

    Parameters
    ----------
    new_parent : configobj.Section
        Section in which information should be added.

    config : configobj.Section
        Section to merge into the new_parent.

    """
    for key, val in config.iteritems():
        if isinstance(val, Section):
            new_parent[key] = {}
            include_configobj(new_parent[key], val)

        else:
            new_parent[key] = val
