# -*- coding: utf-8 -*-
#==============================================================================
# module : test_database.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from hqc_meas.tasks.api import RootTask, SimpleTask, ComplexTask

from ..util import complete_line


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


def test_register_in_database1():
    root = RootTask()
    assert root.get_from_database('threads') == {}
    assert root.get_from_database('instrs') == {}
    assert root.get_from_database('default_path') == ''
