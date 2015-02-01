# -*- coding: utf-8 -*-
# =============================================================================
# module : hqc_meas/tasks/tasks_util/array_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
import logging
from atom.api import (Enum, Str, set_default)
import numpy as np

from ..base_tasks import SimpleTask


class ArrayExtremaTask(SimpleTask):
    """ Store the pair(s) of index/value for the extrema(s) of an array.

    Wait for any parallel operation before execution.

    """
    #: Name of the target in the database.
    target_array = Str().tag(pref=True)

    #: Name of the column into which the extrema should be looked for.
    column_name = Str().tag(pref=True)

    #: Flag indicating which extremum shiul be lookd for.
    mode = Enum('Max', 'Min', 'Max & min').tag(pref=True)

    task_database_entries = set_default({'max_ind': 0, 'max_value': 1.0})

    wait = set_default({'activated': True})  # Wait on all pools by default.

    def perform(self):
        """ Find extrema of database array and store index/value pairs.

        """
        array = self.get_from_database(self.target_array[1:-1])
        if self.column_name:
            array = array[self.column_name]
        if self.mode == 'Max' or self.mode == 'Max & min':
            ind = np.argmax(array)
            val = array[ind]
            self.write_in_database('max_ind', ind)
            self.write_in_database('max_value', val)
        if self.mode == 'Min' or self.mode == 'Max & min':
            ind = np.argmin(array)
            val = array[ind]
            self.write_in_database('min_ind', ind)
            self.write_in_database('min_value', val)

    def check(self, *args, **kwargs):
        """ Check the target array can be found and has the right column.

        """
        test = True
        traceback = {}

        array_entry = self.target_array[1:-1]
        try:
            array = self.get_from_database(array_entry)
        except KeyError:
            traceback[self.task_path + '/' + self.task_name] = \
                '''Invalid entry name for the target array'''
            return False, traceback

        if self.column_name:
            if array.dtype.names:
                if self.column_name not in array.dtype.names:
                    traceback[self.task_path + '/' + self.task_name] = \
                        'No column named {} in array.'.format(self.column_name)
                    return test, traceback
            else:
                test = False
                traceback[self.task_path + '/' + self.task_name] = \
                    'Array has no named columns'
                return test, traceback

        else:
            if array.dtype.names:
                test = False
                mess = 'Must provide a column name for rec arrays.'
                traceback[self.task_path + '/' + self.task_name] = mess
                return test, traceback
            elif len(array.shape) > 1:
                test = False
                mess = 'Must use 1d array when using non rec-arrays.'
                traceback[self.task_path + '/' + self.task_name] = mess
                return test, traceback

        return test, traceback

    def _observe_mode(self, change):
        """ Update the database entries according to the mode.

        """
        if change['value'] == 'Max':
            self.task_database_entries = {'max_ind': 0, 'max_value': 2.0}
        elif change['value'] == 'Min':
            self.task_database_entries = {'min_ind': 0, 'min_value': 1.0}
        else:
            self.task_database_entries = {'max_ind': 0, 'max_value': 2.0,
                                          'min_ind': 0, 'min_value': 1.0}


class ArrayFindValueTask(SimpleTask):
    """ Store the index of the first occurence of a value in an array.

    Wait for any parallel operation before execution.

    """
    #: Name of the target in the database.
    target_array = Str().tag(pref=True)

    #: Name of the column into which the extrema should be looked for.
    column_name = Str().tag(pref=True)

    #: Value which should be looked for in the array.
    value = Str().tag(pref=True)

    task_database_entries = set_default({'index': 0})

    wait = set_default({'activated': True})  # Wait on all pools by default.

    def perform(self):
        """ Find index of value array and store index in database.

        """
        array = self.get_from_database(self.target_array[1:-1])
        if self.column_name:
            array = array[self.column_name]

        val = self.format_and_eval_string(self.value)

        try:
            ind = np.where(np.abs(array - val) < 1e-12)[0][0]
        except IndexError:
            logger = logging.getLogger()
            logger.error('Could not find {} in array {} ({})'.format(val,
                         self.target_array, array))
        self.write_in_database('index', ind)

    def check(self, *args, **kwargs):
        """ Check the target array can be found and has the right column.

        """
        test = True
        traceback = {}
        err_path = self.task_path + '/' + self.task_name

        try:
            self.format_and_eval_string(self.value)
        except Exception as e:
            traceback[err_path + '-value'] = \
                '''Failed to eval value formula : {}'''.format(e)
            test = False

        array_entry = self.target_array[1:-1]
        try:
            array = self.get_from_database(array_entry)
        except KeyError:
            traceback[err_path + '-array'] = \
                '''Invalid entry name for the target array'''
            return False, traceback

        if self.column_name:
            if array.dtype.names:
                if self.column_name not in array.dtype.names:
                    traceback[err_path + '-column'] = \
                        'No column named {} in array.'.format(self.column_name)
                    return test, traceback
            else:
                test = False
                traceback[err_path + '-column'] = \
                    'Array has no named columns'
                return test, traceback

        else:
            if array.dtype.names:
                test = False
                mess = 'Must provide a column name for rec arrays.'
                traceback[err_path + '-column'] = mess
                return test, traceback
            elif len(array.shape) > 1:
                test = False
                mess = 'Must use 1d array when using non rec-arrays.'
                traceback[err_path + '-dim'] = mess
                return test, traceback

        return test, traceback


KNOWN_PY_TASKS = [ArrayExtremaTask, ArrayFindValueTask]
