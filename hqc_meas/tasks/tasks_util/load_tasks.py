# -*- coding: utf-8 -*-
# =============================================================================
# module : load_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import (Bool, Str, Unicode, List, set_default)
import numpy as np
from inspect import cleandoc
import os

from ..base_tasks import SimpleTask
from ..task_interface import InterfaceableTaskMixin, TaskInterface


def _make_array(names, dtypes='f8'):
    if isinstance(dtypes, basestring):
        dtypes = [dtypes for i in range(len(names))]

    dtype = [(name, dtypes[i]) for i, name in enumerate(names)]
    return np.ones((5,), dtype=dtype)


class LoadArrayTask(InterfaceableTaskMixin, SimpleTask):
    """ Load an array from the disc into the database.

    """
    #: Folder from which to load the data.
    folder = Unicode().tag(pref=True)

    #: Name of the file from which to load the data.
    filename = Unicode().tag(pref=True)

    #: Kind of file to load.
    selected_format = Str().tag(pref=True)

    task_database_entries = set_default({'array': _make_array(['var1',
                                                               'var2'])})

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(LoadArrayTask, self).check(*args, **kwargs)
        err_path = self.task_path + '/' + self.task_name

        try:
            full_folder_path = self.format_string(self.folder)
        except Exception as e:
            mess = 'Failed to format the folder path: {}'
            traceback[err_path + '-folder'] = mess.format(e)
            test = False

        try:
            filename = self.format_string(self.filename)
        except Exception as e:
            mess = 'Failed to format the filename: {}'
            traceback[err_path + '-filename'] = mess.format(e)
            test = False

        if not test:
            return test, traceback

        full_path = os.path.join(full_folder_path, filename)

        if not os.path.isfile(full_path):
            traceback[err_path + '-file'] = \
                cleandoc('''File does not exist, be sure that your measurez
                will create before this task is executed.''')

        return test, traceback


KNOWN_PY_TASKS = [LoadArrayTask]


class CSVLoadInterface(TaskInterface):
    """
    """
    #: Delimiter used in the file to load.
    delimiter = Str('\t').tag(pref=True)

    #: Character used to signal a comment.
    comments = Str('#').tag(pref=True)

    #: Flag indicating whether or not to use the first row as column names.
    names = Bool(True).tag(pref=True)

    #: The users can provide the names which will be available in its file
    #: if the file cannot be found when checks are run.
    c_names = List(Str()).tag(pref=True)

    #: Class attr used in the UI.
    file_formats = ['CSV']

    has_view = True

    def perform(self):
        """
        """
        task = self.task
        folder = task.format_string(task.folder)
        filename = task.format_string(task.filename)
        full_path = os.path.join(folder, filename)

        comment_lines = 0
        with open(full_path) as f:
            while True:
                if f.readline().startswith(self.comments):
                    comment_lines += 1
                else:
                    break

        data = np.genfromtxt(full_path, comments=self.comments,
                             delimiter=self.delimiter, names=self.names,
                             skip_header=comment_lines)

        task.write_in_database('array', data)

    def check(self, *args, **kwargs):
        """
        """
        task = self.task
        if self.c_names:
            return True, {}

        try:
            full_folder_path = task.format_string(task.folder)
            filename = task.format_string(task.filename)
        except Exception:
            return True, {}

        full_path = os.path.join(full_folder_path, filename)

        if os.path.isfile(full_path):
            with open(full_path) as f:
                while True:
                    line = f.readline()
                    if not line.startswith(self.comments):
                        names = line.split(self.delimiter)
                        names = [n.strip() for n in names if n]
                        self.task.write_in_database('array',
                                                    _make_array(names))
                        break

        return True, {}

    def _observe_c_names(self, change):
        """ Observer keeping in sync the c_names and the array in the database.

        """
        if change['value']:
            self.task.write_in_database('array', _make_array(change['value']))

INTERFACES = {'LoadArrayTask': [CSVLoadInterface]}
