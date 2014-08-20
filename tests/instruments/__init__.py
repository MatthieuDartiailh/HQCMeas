# -*- coding: utf-8 -*-
import os
from ..util import complete_line, create_test_dir, remove_tree

TEMP_FOLDER = '_temps'


def setup_package():
    print complete_line(__name__ + '__init__.py : setup_package()', '=')
    directory = os.path.dirname(__file__)
    test_dir = os.path.join(directory, TEMP_FOLDER)
    create_test_dir(test_dir)


def teardown_package():
    # Removing .ini files created during tests.
    directory = os.path.dirname(__file__)
    test_dir = os.path.join(directory, TEMP_FOLDER)
    remove_tree(test_dir)
    print complete_line(__name__ + '__init__.py : teardown_package()', '=')
