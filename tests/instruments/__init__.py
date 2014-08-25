# -*- coding: utf-8 -*-
from ..util import complete_line

TEMP_FOLDER = '_temps'


def setup_package():
    print complete_line(__name__ + '__init__.py : setup_package()', '=')


def teardown_package():
    # Removing .ini files created during tests.
    print complete_line(__name__ + '__init__.py : teardown_package()', '=')
