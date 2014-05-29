# -*- coding: utf-8 -*-
#==============================================================================
# module : test_database.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from hqc_meas.tasks.api import RootTask, SimpleTask, ComplexTask
from nose.tools import assert_equal, assert_is, assert_raises

from ..util import complete_line


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


def test_register_in_database1():
    # Check that the root task does write its default entries in the database
    # when instantiated.
    root = RootTask()
    assert_equal(root.get_from_database('threads'), {})
    assert_equal(root.get_from_database('instrs'), {})
    assert_equal(root.get_from_database('default_path'), '')


def test_child_addition_handling1():
    # Test that adding a task to the root task is correctly handled.
    root = RootTask()
    task1 = ComplexTask(task_name='task1',
                        task_database_entries={'val1': 2.0})
    root.children_task.append(task1)

    assert_equal(task1.task_depth, 1)
    assert_equal(task1.task_path, 'root')
    assert_is(task1.task_database, root.task_database)
    assert_is(task1.root_task, root)
    assert_is(task1.parent_task, root)

    assert_equal(task1.get_from_database('task1_val1'), 2.0)
    assert_equal(root.get_from_database('task1_val1'), 2.0)


def test_child_addition_handling2():
    # Test that adding a task to a complex task below the root task is
    #correctly handled.
    root = RootTask()
    task1 = ComplexTask(task_name='task1',
                        task_database_entries={'val1': 2.0})
    root.children_task.append(task1)
    task2 = SimpleTask(task_name='task2',
                       task_database_entries={'val2': 'r'})
    task1.children_task.append(task2)

    assert_equal(task2.task_depth, 2)
    assert_equal(task2.task_path, 'root/task1')
    assert_is(task2.task_database, root.task_database)
    assert_is(task2.root_task, root)
    assert_is(task2.parent_task, task1)

    assert_equal(task2.get_from_database('task2_val2'), 'r')


def test_giving_root1():
    # Test assembling a hierarchy and giving it a root task only later.
    root = RootTask()

    task1 = ComplexTask(task_name='task1')
    task2 = ComplexTask(task_name='task2')
    task1.children_task.append(task2)
    task3 = ComplexTask(task_name='task3')
    task2.children_task.append(task3)
    task4 = SimpleTask(task_name='task4',
                       task_database_entries={'val2': 'r'})
    task3.children_task.append(task4)

    task3.access_exs = ['task4_val2']
    task2.access_exs = ['task4_val2']

    root.children_task.append(task1)

    assert_equal(root.get_from_database('task4_val2'), 'r')
    task3.children_task = []
    assert_raises(KeyError, root.get_from_database, 'task4_val2')
    task3.children_task.append(task4)
    assert_equal(root.get_from_database('task4_val2'), 'r')


def test_ex_access_handling1():
    # Test adding an ex_access for an entry.
    root = RootTask()
    task1 = ComplexTask(task_name='task1')
    root.children_task.append(task1)
    task2 = SimpleTask(task_name='task2',
                       task_database_entries={'val2': 'r'})
    task1.children_task.append(task2)

    task1.add_access_exception('task2_val2')
    assert_equal(root.get_from_database('task2_val2'), 'r')


def test_ex_access_handling2():
    # Test removing an ex_access for an entry.
    root = RootTask()
    task1 = ComplexTask(task_name='task1')
    root.children_task.append(task1)
    task2 = SimpleTask(task_name='task2',
                       task_database_entries={'val2': 'r'})
    task1.children_task.append(task2)

    task1.add_access_exception('task2_val2')
    assert_equal(root.get_from_database('task2_val2'), 'r')
    task1.remove_access_exception('task2_val2')
    assert_raises(KeyError, root.get_from_database, 'task2_val2')


def test_ex_access_handling3():
    # Test moving a task with whose one entry has an ex_access.
    root = RootTask()
    task1 = ComplexTask(task_name='task1')
    root.children_task.append(task1)
    task2 = SimpleTask(task_name='task2',
                       task_database_entries={'val2': 'r'})
    task1.children_task.append(task2)

    task1.add_access_exception('task2_val2')
    assert_equal(root.get_from_database('task2_val2'), 'r')
    task1.children_task = []
    assert_raises(KeyError, root.get_from_database, 'task2_val2')
    task1.children_task.append(task2)
    assert_equal(root.get_from_database('task2_val2'), 'r')


def test_ex_access_handling4():
    # Test removing a task with whose one entry has an ex_access, adding a new
    # one and re-adding the first.
    root = RootTask()
    task1 = ComplexTask(task_name='task1')
    root.children_task.append(task1)
    task2 = SimpleTask(task_name='task2',
                       task_database_entries={'val2': 'r'})
    task1.children_task.append(task2)

    task1.add_access_exception('task2_val2')
    assert_equal(root.get_from_database('task2_val2'), 'r')
    task1.children_task = []
    assert_raises(KeyError, root.get_from_database, 'task2_val2')
    task3 = SimpleTask(task_name='task3',
                       task_database_entries={'val3': 'r'})
    task1.children_task.append(task3)
    task1.children_task.append(task2)
    assert_raises(KeyError, root.get_from_database, 'task2_val2')


def test_ex_access_handling5():
    # Test removing a task with whose one entry has an ex_access, and then
    # adding a different task (same name, same class, etc)
    root = RootTask()
    task1 = ComplexTask(task_name='task1')
    root.children_task.append(task1)
    task2 = SimpleTask(task_name='task2',
                       task_database_entries={'val2': 'r'})
    task1.children_task.append(task2)

    task1.add_access_exception('task2_val2')
    assert_equal(root.get_from_database('task2_val2'), 'r')
    task1.children_task = []
    assert_raises(KeyError, root.get_from_database, 'task2_val2')
    task3 = SimpleTask(task_name='task2',
                       task_database_entries={'val2': 'r'})
    task1.children_task.append(task3)
    assert_raises(KeyError, root.get_from_database, 'task2_val2')


def test_ex_access_handling6():
    # Test moving a task to which two access exs are linked.
    root = RootTask()
    task1 = ComplexTask(task_name='task1')
    root.children_task.append(task1)
    task2 = ComplexTask(task_name='task2')
    task1.children_task.append(task2)
    task3 = ComplexTask(task_name='task3')
    task2.children_task.append(task3)
    task4 = SimpleTask(task_name='task4',
                       task_database_entries={'val2': 'r'})
    task3.children_task.append(task4)

    task3.add_access_exception('task4_val2')
    task2.add_access_exception('task4_val2')
    assert_equal(root.get_from_database('task4_val2'), 'r')
    task3.children_task = []
    assert_raises(KeyError, root.get_from_database, 'task4_val2')
    task3.children_task.append(task4)
    assert_equal(root.get_from_database('task4_val2'), 'r')
