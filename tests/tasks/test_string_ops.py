# -*- coding: utf-8 -*-
#==============================================================================
# module : test_string_formatting.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from nose.tools import assert_in, assert_equal, assert_false, assert_true
from hqc_meas.tasks.base_tasks import RootTask
from math import cos
import numpy
from numpy.testing import assert_array_equal
from ..util import complete_line


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


class TestFormatting(object):

    def setup(self):
        self.root = RootTask()
        database = self.root.task_database
        database.set_value('root', 'val1', 1)
        database.create_node('root', 'node1')
        database.set_value('root/node1', 'val2', 10.0)
        database.add_access_exception('root', 'val2', 'root/node1')

    def test_formatting_editing_mode1(self):
        test = 'progress is {val1}/{val2}, it is good.'
        formatted = self.root.format_string(test)
        assert_equal(formatted, 'progress is 1/10.0, it is good.')
        assert_false(self.root._format_cache)

    def test_formatting_editing_mode2(self):
        test = 'progress is {val1}/{val2}'
        formatted = self.root.format_string(test)
        assert_equal(formatted, 'progress is 1/10.0')
        assert_false(self.root._format_cache)

    def test_formatting_editing_mode3(self):
        test = '{val1}/{val2}, it is good.'
        formatted = self.root.format_string(test)
        assert_equal(formatted, '1/10.0, it is good.')
        assert_false(self.root._format_cache)

    def test_formatting_editing_mode4(self):
        test = '{val1}/{val2}'
        formatted = self.root.format_string(test)
        assert_equal(formatted, '1/10.0')
        assert_false(self.root._format_cache)

    def test_formatting_running_mode1(self):
        self.root.task_database.prepare_for_running()
        test = 'progress is {val1}/{val2}, it is good.'
        formatted = self.root.format_string(test)
        assert_equal(formatted, 'progress is 1/10.0, it is good.')
        assert_true(self.root._format_cache)
        assert_in(test, self.root._format_cache)
        self.root.task_database.set_value('root', 'val1', 2)
        formatted = self.root.format_string(test)
        assert_equal(formatted, 'progress is 2/10.0, it is good.')

    def test_formatting_running_mode2(self):
        self.root.task_database.prepare_for_running()
        test = 'progress is {val1}/{val2}'
        formatted = self.root.format_string(test)
        assert_equal(formatted, 'progress is 1/10.0')
        assert_true(self.root._format_cache)
        assert_in(test, self.root._format_cache)
        self.root.task_database.set_value('root', 'val1', 2)
        formatted = self.root.format_string(test)
        assert_equal(formatted, 'progress is 2/10.0')

    def test_formatting_running_mode3(self):
        self.root.task_database.prepare_for_running()
        test = '{val1}/{val2}, it is good.'
        formatted = self.root.format_string(test)
        assert_equal(formatted, '1/10.0, it is good.')
        assert_true(self.root._format_cache)
        assert_in(test, self.root._format_cache)
        self.root.task_database.set_value('root', 'val1', 2)
        formatted = self.root.format_string(test)
        assert_equal(formatted, '2/10.0, it is good.')

    def test_formatting_running_mode4(self):
        self.root.task_database.prepare_for_running()
        test = '{val1}/{val2}'
        formatted = self.root.format_string(test)
        assert_equal(formatted, '1/10.0')
        assert_true(self.root._format_cache)
        assert_in(test, self.root._format_cache)
        self.root.task_database.set_value('root', 'val1', 2)
        formatted = self.root.format_string(test)
        assert_equal(formatted, '2/10.0')


class TestEvaluation(object):

    def setup(self):
        self.root = RootTask()
        database = self.root.task_database
        database.set_value('root', 'val1', 1)
        database.create_node('root', 'node1')
        database.set_value('root/node1', 'val2', 10.0)
        database.add_access_exception('root', 'val2', 'root/node1')

    def test_eval_editing_mode1(self):
        test = '{val1}/{val2}'
        formatted = self.root.format_and_eval_string(test)
        assert_equal(formatted, 0.1)
        assert_false(self.root._eval_cache)

    def test_eval_editing_mode2(self):
        test = 'cos({val1}/{val2})'
        formatted = self.root.format_and_eval_string(test)
        assert_equal(formatted, cos(0.1))
        assert_false(self.root._eval_cache)

    def test_eval_editing_mode3(self):
        self.root.task_database.set_value('root', 'val1', 10.0)
        test = 'cm.sqrt({val1}/{val2})'
        formatted = self.root.format_and_eval_string(test)
        assert_equal(formatted, 1+0j)
        assert_false(self.root._eval_cache)

    def test_eval_editing_mode4(self):
        self.root.task_database.set_value('root', 'val1', [1.0, -1.0])
        test = 'np.abs({val1})'
        formatted = self.root.format_and_eval_string(test)
        assert_array_equal(formatted, numpy.array((1.0, 1.0)))
        assert_false(self.root._eval_cache)

    def test_eval_running_mode1(self):
        self.root.task_database.prepare_for_running()
        test = '{val1}/{val2}'
        formatted = self.root.format_and_eval_string(test)
        assert_equal(formatted, 0.1)
        assert_true(self.root._eval_cache)
        assert_in(test, self.root._eval_cache)
        self.root.task_database.set_value('root', 'val1', 2)
        formatted = self.root.format_and_eval_string(test)
        assert_equal(formatted, 0.2)

    def test_eval_running_mode2(self):
        self.root.task_database.prepare_for_running()
        test = 'cos({val1}/{val2})'
        formatted = self.root.format_and_eval_string(test)
        assert_equal(formatted, cos(0.1))
        assert_true(self.root._eval_cache)
        assert_in(test, self.root._eval_cache)
        self.root.task_database.set_value('root', 'val1', 2)
        formatted = self.root.format_and_eval_string(test)
        assert_equal(formatted, cos(0.2))

    def test_eval_running_mode3(self):
        self.root.task_database.prepare_for_running()
        self.root.task_database.set_value('root', 'val1', 10.0)
        test = 'cm.sqrt({val1}/{val2})'
        formatted = self.root.format_and_eval_string(test)
        assert_equal(formatted, (1+0j))
        assert_true(self.root._eval_cache)
        assert_in(test, self.root._eval_cache)
        self.root.task_database.set_value('root', 'val1', 40.0)
        formatted = self.root.format_and_eval_string(test)
        assert_equal(formatted, (2+0j))

    def test_eval_running_mode4(self):
        self.root.task_database.prepare_for_running()
        self.root.task_database.set_value('root', 'val1', [1.0, -1.0])
        test = 'np.abs({val1})'
        formatted = self.root.format_and_eval_string(test)
        assert_array_equal(formatted, numpy.array((1.0, 1.0)))
        assert_true(self.root._eval_cache)
        assert_in(test, self.root._eval_cache)
        self.root.task_database.set_value('root', 'val1', [2.0, -1.0])
        self.root.task_database.set_value('root', 'val2', 0)
        test = 'np.abs({val1})[{val2}]'
        formatted = self.root.format_and_eval_string(test)
        assert_equal(formatted, 2.0)
