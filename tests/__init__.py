# -*- coding: utf-8 -*-
#==============================================================================
# module : __init__.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from __future__ import print_function
import sys, os
from enaml.qt.qt_application import QtApplication

from .util import complete_line


def setup_package():
    sys.path.append('..')
    QtApplication()
    print('')
    print(complete_line(__name__ + '__init__.py : setup_package()', '='))
    directory = os.path.dirname(__file__)
    util_path = os.path.join(directory, '..', 'hqc_meas', 'utils',
                             'preferences')
    def_path = os.path.join(util_path, 'default.ini')
    if os.path.isfile(def_path):
        os.rename(def_path, os.path.join(util_path, '_user_default.ini'))


def teardown_package():
    directory = os.path.dirname(__file__)
    util_path = os.path.join(directory, '..', 'hqc_meas', 'utils',
                             'preferences')
    def_path = os.path.join(util_path, 'default.ini')
    safe_path = os.path.join(util_path, '_user_default.ini')
    if os.path.isfile(def_path):
        os.remove(def_path)
    if os.path.isfile(safe_path):
        os.rename(safe_path, def_path)
    print(complete_line(__name__ + '__init__.py : teardown_package()', '='))
