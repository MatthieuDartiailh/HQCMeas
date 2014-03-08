# -*- coding: utf-8 -*-
#==============================================================================
# module : instrument_manager.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
import os
from configobj import ConfigObj


def open_profile(profile_path):
    """ Access the profile specified

    Parameters
    ----------
    profile_path : unicode
        Path to the file in which the profile is stored

    """
    return ConfigObj(profile_path).dict()


def save_profile(directory, profile_name, profile_infos):
    """ Save a profile to a file

    Parameters
    ----------
    profile_path : unicode
        Path of the file to which the profile should be saved

    profiles_infos : dict
        Dict containing the profiles infos
    """
    path = os.path.join(directory, profile_name + '.ini')
    conf = ConfigObj()
    conf.update(profile_infos)
    conf.write(path)
