# -*- coding: utf-8 -*-
from configobj import ConfigObj
from nose.tools import with_setup
from inspect import cleandoc
from textwrap import wrap
import os

from hqc_meas.task_management.templates import load_template, save_template

from ..util import complete_line


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


def setup():
    local_dir = os.path.dirname(__file__)
    local_file = os.path.join(local_dir, 'test.ini')
    config = ConfigObj(local_file)
    config.initial_comment = ['test line 1', 'test line 2']
    config['test'] = "{'test': 1.0}"
    config.write()


def teardown():
    local_dir = os.path.dirname(__file__)
    for fi in os.listdir(local_dir):
        if fi.endswith('.ini'):
            os.remove(os.path.join(local_dir, fi))


@with_setup(setup, teardown)
def test_load():
    local_dir = os.path.dirname(__file__)
    local_file = os.path.join(local_dir, 'test.ini')
    test_load = load_template(local_file)
    assert test_load[0]['test'] == "{'test': 1.0}"
    assert test_load[1] == 'test line 1\ntest line 2'


@with_setup(setup, teardown)
def test_save():
    local_dir = os.path.dirname(__file__)
    data = {'a': 1.0}
    doc = cleandoc(''' This is a long test ...................................
                    .........................................................
                    .........................................................
                    ''')
    path = os.path.join(local_dir, 'test2.ini')
    save_template(path, data, doc)

    assert os.path.isfile(path)
    conf = ConfigObj(path)
    assert conf['a'] == '1.0'
    assert conf.initial_comment == ['# ' + line for line in wrap(doc, 79)]
