# -*- coding: utf-8 -*-
from nose.tools import assert_equal
from hqc_meas.tasks.tools.walks import flatten_walk


def test_flatten_walk():
    walk = [{'e': 1, 'a': 2},
            [{'e': 1, 'z': 5}, {'e': 2}, [{'x': 50}]]]
    flat = flatten_walk(walk, ['e', 'x'])
    assert_equal(flat, {'e': set((1, 2)), 'x': set([50])})
