# -*- coding: utf-8 -*-
#==============================================================================
# module : test_configobj_ops.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
import os
from configobj import ConfigObj
from nose.tools import assert_equal, assert_in

from hqc_meas.utils.configobj_ops import flatten_config


def test_flatten_configobj():
    """

    """
    config = ConfigObj(os.path.join(os.path.dirname(__file__),
                       'config_test.ini'))

    flat = flatten_config(config, ['task_class', 'selected_profile'])
    assert_in('task_class', flat)
    assert_equal(flat['task_class'],
                 set(['ComplexTask', 'SaveTask', 'LoopTask',
                      'LockInMeasureTask', 'RFSourceSetFrequencyTask',
                      'FormulaTask']))

    assert_in('selected_profile', flat)
    assert_equal(flat['selected_profile'],
                 set(['Lock8', 'Lock12', 'RF19']))
