# -*- coding: utf-8 -*-
#==============================================================================
# module : __init__.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from __future__ import print_function
import sys


def setup_package():
    sys.path.append('..')
    print('')
    print(__name__, '__init__.py : setup_package() ==========================')


def teardown_package():
    print(__name__, '__init__.py : teardown_package() =======================')
