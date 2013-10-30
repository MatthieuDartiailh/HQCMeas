# -*- coding: utf-8 -*-
#==============================================================================
# module : __init__.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
This module gives an easy access to the path of the profiles folder where the
profiles of the instrument, containing the necessary informations to open a
connection, are stored.

:Contains:
    PROFILES_DIRECTORY_PATH

"""
import os
PROFILES_DIRECTORY_PATH = os.path.dirname(__file__)