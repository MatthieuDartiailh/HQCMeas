# -*- coding: utf-8 -*-

from ...util import complete_line


def setup_package():
    print complete_line(__name__ + '__init__.py : setup_package()', '=')


def teardown_package():
    print complete_line(__name__ + '__init__.py : teardown_package()', '=')