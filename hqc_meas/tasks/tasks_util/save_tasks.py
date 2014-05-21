# -*- coding: utf-8 -*-
#==============================================================================
# module : save_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from atom.api import (Tuple, ContainerList, Str, Enum, Value,
                      Bool, Int, observe, set_default, Unicode)

import os
import numpy
import logging
from inspect import cleandoc

from ..tools.database_string_formatter import (get_formatted_string,
                                               format_and_eval_string)
from ..base_tasks import SimpleTask


class SaveTask(SimpleTask):
    """ Save the specified entries either in a CSV file or an array.

    Wait for any parallel operation before execution.

    Notes
    -----
    Currently only support saving floats.

    """
    # Folder in which to save the data.
    folder = Unicode().tag(pref=True)

    # Name of the file in which to write the data.
    filename = Str().tag(pref=True)

    # Currently opened file object. (File mode)
    file_object = Value()

    # Header to write at the top of the file.
    header = Str().tag(pref=True)

    # Numpy array in which data are stored (Array mode)
    array = Value()  # Array

    # Kind of object in which to save the data.
    saving_target = Enum('File', 'Array', 'File and array').tag(pref=True)

    # Size of the data to be saved. (Evaluated at runtime)
    array_size = Str().tag(pref=True)

    # Computed size of the data (post evaluation)
    array_length = Int()

    # Index of the current line.
    line_index = Int(0)

    # List of values to be saved store as (label, value).
    saved_values = ContainerList(Tuple()).tag(pref=True)

    # Flag indicating whether or not initialisation has been performed.
    initialized = Bool(False)

    task_database_entries = set_default({'file': None})

    def __init__(self, **kwargs):
        super(SaveTask, self).__init__(**kwargs)
        self.make_wait()

    def process(self):
        """ Collect all data and write them to array or file according to mode.

        On first call initialise the systemby creating file and/or array. Close
        file when the expected number of lines has been written.

        """
        #Initialisation.
        if not self.initialized:
            self.line_index = 0
            self.array_length = format_and_eval_string(self.array_size,
                                                       self.task_path,
                                                       self.task_database)
            if self.saving_target != 'Array':
                full_folder_path = get_formatted_string(self.folder,
                                                        self.task_path,
                                                        self.task_database)

                filename = get_formatted_string(self.filename,
                                                self.task_path,
                                                self.task_database)

                full_path = os.path.join(full_folder_path, filename)
                try:
                    self.file_object = open(full_path, 'w')
                except IOError:
                    log = logging.getLogger()
                    mes = cleandoc('''In {}, failed to open the specified
                                    file'''.format(self.task_name))
                    log.error(mes)
                    self.root_task.should_stop.set()
                    return False

                self.write_in_database('file', self.file_object)
                if self.header:
                    for line in self.header.split('\n'):
                        self.file_object.write('# ' + line + '\n')
                labels = [s[0] for s in self.saved_values]
                self.file_object.write('\t'.join(labels) + '\n')
                self.file_object.flush()

            if self.saving_target != 'File':
                # TODO add more flexibilty on the dtype (possible complex
                # values)
                array_type = numpy.dtype([(str(s[0]), 'f8')
                                          for s in self.saved_values])
                self.array = numpy.empty((self.array_length),
                                         dtype=array_type)
                self.write_in_database('array', self.array)
            self.initialized = True

        #writing
        values = [format_and_eval_string(s[1],
                                         self.task_path,
                                         self.task_database)
                  for s in self.saved_values]
        if self.saving_target != 'Array':
            self.file_object.write('\t'.join([str(val)
                                              for val in values]) + '\n')
            self.file_object.flush()
        if self.saving_target != 'File':
            self.array[self.line_index] = tuple(values)

        self.line_index += 1

        #Closing
        if self.line_index == self.array_length:
            self.write_in_database('array', self.array)
            self.file_object.close()
            self.initialized = False

        return True

    def check(self, *args, **kwargs):
        """
        """
        traceback = {}
        if self.saving_target != 'Array':
            try:
                full_folder_path = get_formatted_string(self.folder,
                                                        self.task_path,
                                                        self.task_database)
            except Exception:
                traceback[self.task_path + '/' + self.task_name] = \
                    'Failed to format the folder path'
                return False, traceback

            try:
                filename = get_formatted_string(self.filename, self.task_path,
                                                self.task_database)
            except Exception:
                traceback[self.task_path + '/' + self.task_name] = \
                    'Failed to format the filename'
                return False, traceback

            full_path = os.path.join(full_folder_path, filename)

            try:
                f = open(full_path, 'wb')
                f.close()
            except Exception:
                traceback[self.task_path + '/' + self.task_name] = \
                    'Failed to open the specified file'
                return False, traceback

        try:
            format_and_eval_string(self.array_size,
                                   self.task_path,
                                   self.task_database)
        except Exception:
            traceback[self.task_path + '/' + self.task_name] = \
                'Failed to compute the array size'
            return False, traceback

        test = True
        for i, s in enumerate(self.saved_values):
            try:
                format_and_eval_string(s[1],
                                       self.task_path,
                                       self.task_database)
            except Exception as e:
                traceback[self.task_path + '/' + self.task_name + str(i)] = \
                    'Failed to evaluate entry {}: {}'.format(s[0], e)
                test = False

        if self.saving_target != 'File':
            data = [numpy.array([0.0, 1.0]) for s in self.saved_values]
            names = str(','.join([s[0] for s in self.saved_values]))
            final_arr = numpy.rec.fromarrays(data, names=names)

            self.write_in_database('array', final_arr)

        return test, traceback

    @observe('saving_target')
    def _update_database_entries(self, change):
        """
        """
        new = change['value']
        if new == 'File':
            self.task_database_entries = {'file': None}
        elif new == 'Array':
            self.task_database_entries = {'array': numpy.array([1.0])}
        else:
            self.task_database_entries = {'file': None,
                                          'array': numpy.array([1.0])}


class SaveArrayTask(SimpleTask):
    """Save the specified array either in a CSV file or as a .npy binary file.

    Wait for any parallel operation before execution.

    """

    # Folder in which to save the data.
    folder = Unicode().tag(pref=True)

    # Name of the file in which to write the data.
    filename = Str().tag(pref=True)

    # Currently opened file object.
    file_object = Value()

    # Header to write at the top of the file.
    header = Str().tag(pref=True)

    # Name of the array to save in the database.
    target_array = Str().tag(pref=True)

    # Flag indicating whether to save as csv or .npy.
    mode = Enum('Text file', 'Binary file').tag(pref=True)

    def __init__(self, **kwargs):
        super(SaveArrayTask, self).__init__(**kwargs)
        self.make_wait()

    def process(self):
        """ Save array to file.

        """
        array_to_save = self.get_from_database(self.target_array[1:-1])

        full_folder_path = get_formatted_string(self.folder,
                                                self.task_path,
                                                self.task_database)

        filename = get_formatted_string(self.filename,
                                        self.task_path,
                                        self.task_database)

        full_path = os.path.join(full_folder_path, filename)

        if self.mode == 'Text file':
            try:
                self.file_object = open(full_path, 'wb')
            except IOError:
                mes = cleandoc('''In {}, failed to open the specified
                                file'''.format(self.task_name))
                log = logging.getLogger()
                log.error(mes)

                self.root_task.should_stop.set()
                return

            if self.header:
                for line in self.header.split('\n'):
                    self.file_object.write('# ' + line + '\n')
            if array_to_save.dtype.names:
                self.file_object.write('\t'.join(array_to_save.dtype.names) +
                                       '\n')
            numpy.savetxt(self.file_object, array_to_save, delimiter='\t')
            self.file_object.close()

        else:
            try:
                self.file_object = open(full_path, 'wb')
                self.file_object.close()
            except IOError:
                mes = cleandoc(''''In {}, failed to open the specified
                                file'''.format(self.task_name))
                log = logging.getLogger()
                log.error(mes)

                self.root_task.should_stop.set()
                return

            numpy.save(full_path, array_to_save)

    def check(self, *args, **kwargs):
        """ Check folder path and filename.

        """
        traceback = {}
        try:
            full_folder_path = get_formatted_string(self.folder,
                                                    self.task_path,
                                                    self.task_database)
        except Exception:
            traceback[self.task_path + '/' + self.task_name] = \
                'Failed to format the folder path'
            return False, traceback

        if self.mode == 'Binary file':
            if len(self.filename) > 3:
                if self.filename[-4] == '.' and self.filename[-3:] != 'npy':
                    self.filename = self.filename[:-4] + '.npy'
                    log = logging.getLogger()
                    mes = cleandoc("""The extension of the file will be
                                    replaced by '.npy' in task
                                    {}""".format(self.task_name))
                    log.info(mes)

        try:
            filename = get_formatted_string(self.filename, self.task_path,
                                            self.task_database)
        except Exception:
            traceback[self.task_path + '/' + self.task_name] = \
                'Failed to format the filename'
            return False, traceback

        full_path = os.path.join(full_folder_path, filename)

        try:
            f = open(full_path, 'wb')
            f.close()
        except Exception:
            traceback[self.task_path + '/' + self.task_name] = \
                'Failed to open the specified file'
            return False, traceback

        entries = self.task_database.list_accessible_entries(self.task_path)
        if self.target_array[1:-1] not in entries:
            traceback[self.task_path + '/' + self.task_name] = \
                'Specified array is absent from the database'
            return False, traceback

        return True, traceback

KNOWN_PY_TASKS = [SaveTask, SaveArrayTask]
