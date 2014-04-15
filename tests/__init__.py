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
from enaml.qt.qt_application import QtApplication

from .util import complete_line


def setup_package():
    sys.path.append('..')
    QtApplication()
    print('')
    print(complete_line(__name__ + '__init__.py : setup_package()', '='))


def teardown_package():
    print(complete_line(__name__ + '__init__.py : teardown_package()', '='))
