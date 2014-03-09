# -*- coding: utf-8 -*-
#==============================================================================
# module : test_database.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from nose.tools import raises
from hqc_meas.tasks.tools.task_database import TaskDatabase


def test_database_nodes():
    database = TaskDatabase()
    database.create_node('root', 'node1')
    database.create_node('root/node1', 'node2')
    database.rename_node('root', 'n_node1', 'node1')
    database.delete_node('root/n_node1', 'node2')


def test_database_values():
    database = TaskDatabase()
    database.set_value('root', 'val1', 1)
    assert database.get_value('root', 'val1') == 1
    database.create_node('root', 'node1')
    database.set_value('root/node1', 'val2', 'a')
    assert database.get_value('root/node1', 'val2') == 'a'
    assert database.get_value('root/node1', 'val1') == 1


@raises(KeyError)
def test_database_values2():
    database = TaskDatabase()
    database.set_value('root', 'val1', 1)
    assert database.get_value('root', 'val1') == 1
    database.delete_value('root', 'val1')
    database.get_value('root', 'val1')


def test_database_listing():
    database = TaskDatabase()
    database.set_value('root', 'val1', 1)
    database.create_node('root', 'node1')
    database.set_value('root/node1', 'val2', 'a')

    assert database.list_all_entries() ==\
        sorted(['root/val1', 'root/node1/val2'])
    assert database.list_accessible_entries('root') == ['val1']
    assert database.list_accessible_entries('root/node1') ==\
        sorted(['val1', 'val2'])

    database.excluded = ['val1']
    print database.list_all_entries()
    assert database.list_all_entries() ==\
        sorted(['root/node1/val2'])
    assert database.list_accessible_entries('root') == []
    assert database.list_accessible_entries('root/node1') ==\
        sorted(['val2'])
