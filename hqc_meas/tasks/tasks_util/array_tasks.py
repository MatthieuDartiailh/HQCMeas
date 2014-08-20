# -*- coding: utf-8 -*-
# =============================================================================
# module : array_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import (Str, set_default, Enum)
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

    wait = set_default({'no_wait': []})  # Wait on all pools by default.

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
                    test = False
                    traceback[self.task_path + '/' + self.task_name] = \
                        'No column named {} in array'.format(self.column_name)
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
                traceback[self.task_path + '/' + self.task_name] = \
                    mess.format(self.column_name)
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

KNOWN_PY_TASKS = [ArrayExtremaTask]
