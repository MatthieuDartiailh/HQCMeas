# -*- coding: utf-8 -*-
"""
"""

from traits.api import (Str, on_trait_change, Enum)
from traitsui.api import (View, Group, VGroup, UItem, LineCompleterEditor,
                          Label)

import numpy as np

from .tools.task_decorator import (make_stoppable, make_wait)
from .base_tasks import SimpleTask

class ArrayExtremaTask(SimpleTask):
    """Store in the database the pair(s) of index/value for the extrema(s) of an
    array. Wait for any parallel operation before execution.
    """
    target_array = Str(preference = True)
    column_name = Str(preference = True)
    mode = Enum('Max', 'Min', 'Max & min', preference = True)

    task_database_entries = {'max_ind' : 0, 'max_value' : 1.0}

    def __init__(self, *args, **kwargs):
        super(ArrayExtremaTask, self).__init__(*args, **kwargs)
        self._define_task_view()

    @make_stoppable
    @make_wait()
    def process(self):
        """
        """
        array = self.get_from_database(self.target_array[1:-1])
        if self.column_name:
            array = array[self.column_name]
        if self.mode == 'Max' or self.mode == 'Max & min':
            ind = np.argmax(array)
            val = array[ind]
            self.write_in_database('max_ind', ind)
            self.write_in_database('max_value', val)
        if  self.mode == 'Min' or self.mode == 'Max & min':
            ind = np.argmin(array)
            val = array[ind]
            self.write_in_database('min_ind', ind)
            self.write_in_database('min_value', val)


    def check(self, *args, **kwargs):
        """
        """
        test = True
        traceback = {}

        entries = self.task_database.list_accessible_entries(self.task_path)
        array_entry = self.target_array[1:-1]
        if array_entry not in entries:
            traceback[self.task_path + '/' + self.task_name] = \
                '''Invalid entry name for the target array'''
            return False, traceback

        if self.column_name:
            array = self.get_from_database(array_entry)
            if array.dtype.names:
                if self.column_name not in array.dtype.names:
                    test = False
                    traceback[self.task_path + '/' + self.task_name] = \
                        'No column named {} in array'.format(self.column_name)
            else:
                test = False
                traceback[self.task_path + '/' + self.task_name] = \
                        'Array has no named columns'

        return test, traceback

    @on_trait_change('mode')
    def _new_selected_mode(self, new):
        """
        """
        if new == 'Max':
            self.task_database_entries = {'max_ind' : 0, 'max_value' : 1.0}
        elif new == 'Min':
            self.task_database_entries = {'min_ind' : 0, 'min_value' : -1.0}
        else:
            self.task_database_entries = {'max_ind' : 0, 'max_value' : 1.0,
                                          'min_ind' : 0, 'min_value' : -1.0}

    def _list_database_entries(self):
        """
        """
        entries =  self.task_database.list_accessible_entries(self.task_path)
        return entries

    def _define_task_view(self):
        """
        """
        line_completer = LineCompleterEditor(
                             entries_updater = self._list_database_entries)
        view = View(
                    VGroup(
                        UItem('task_name', style = 'readonly'),
                        Group(
                            Label('Array'), Label('Column name'),
                            Label('Mode'),
                            UItem('target_array', editor = line_completer),
                            UItem('column_name'),
                            UItem('mode'),
                            columns = 3,
                            show_border = True,
                            ),
                        ),
                     )

        self.trait_view('task_view', view)
