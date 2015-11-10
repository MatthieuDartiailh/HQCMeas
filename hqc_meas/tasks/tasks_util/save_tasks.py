# -*- coding: utf-8 -*-
# =============================================================================
# module : save_tasks.py
# author : Matthieu Dartiailh & Sébastien Jezouin
# license : MIT license
# =============================================================================
"""
"""
from atom.api import (Tuple, ContainerList, Str, Enum, Value,
                      Bool, Int, observe, set_default, Unicode)
import os
import errno
import numpy
import h5py
import logging
from inspect import cleandoc

from ..base_tasks import SimpleTask


class SaveTask(SimpleTask):
    """ Save the specified entries either in a CSV file or an array. The file
    is closed when the line number is reached.

    Wait for any parallel operation before execution.

    Notes
    -----
    Currently only support saving floats.

    """
    #: Kind of object in which to save the data.
    saving_target = Enum('File', 'Array', 'File and array').tag(pref=True)

    #: Folder in which to save the data.
    folder = Unicode().tag(pref=True)

    #: Name of the file in which to write the data.
    filename = Unicode().tag(pref=True)

    #: Currently opened file object. (File mode)
    file_object = Value()

    #: Opening mode to use when saving to a file.
    file_mode = Enum('New', 'Add')

    #: Header to write at the top of the file.
    header = Str().tag(pref=True)

    #: Numpy array in which data are stored (Array mode)
    array = Value()  # Array

    #: Size of the data to be saved. (Evaluated at runtime)
    array_size = Str().tag(pref=True)

    #: Computed size of the data (post evaluation)
    array_length = Int()

    #: Index of the current line.
    line_index = Int(0)

    #: List of values to be saved store as (label, value).
    saved_values = ContainerList(Tuple()).tag(pref=True)

    #: Flag indicating whether or not initialisation has been performed.
    initialized = Bool(False)

    task_database_entries = set_default({'file': None})

    wait = set_default({'activated': True})  # Wait on all pools by default.

    def perform(self):
        """ Collect all data and write them to array or file according to mode.

        On first call initialise the system by opening file and/or array. Close
        file when the expected number of lines has been written.

        """
        # Initialisation.
        if not self.initialized:

            self.line_index = 0
            size_str = self.array_size
            if size_str:
                self.array_length = self.format_and_eval_string(size_str)
            else:
                self.array_length = -1

            if self.saving_target != 'Array':
                full_folder_path = self.format_string(self.folder)
                filename = self.format_string(self.filename)
                full_path = os.path.join(full_folder_path, filename)
                mode = 'wb' if self.file_mode == 'New' else 'ab'

                try:
                    self.file_object = open(full_path, mode)
                except IOError as e:
                    log = logging.getLogger()
                    mes = cleandoc('''In {}, failed to open the specified
                                    file {}'''.format(self.task_name, e))
                    log.error(mes)
                    self.root_task.should_stop.set()

                self.root_task.files[full_path] = self.file_object
                if self.header:
                    h = self.format_string(self.header)
                    for line in h.split('\n'):
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

        # Writing
        values = [self.format_and_eval_string(s[1])
                  for s in self.saved_values]
        if self.saving_target != 'Array':
            self.file_object.write('\t'.join([str(val)
                                              for val in values]) + '\n')
            self.file_object.flush()
        if self.saving_target != 'File':
            self.array[self.line_index] = tuple(values)

        self.line_index += 1

        # Closing
        if self.line_index == self.array_length:
            if self.file_object:
                self.file_object.close()
            self.initialized = False

    def check(self, *args, **kwargs):
        """
        """
        err_path = self.task_path + '/' + self.task_name
        traceback = {}
        if self.saving_target != 'Array':
            try:
                full_folder_path = self.format_string(self.folder)
            except Exception as e:
                mess = 'Failed to format the folder path: {}'
                traceback[err_path] = mess.format(e)
                return False, traceback

            try:
                filename = self.format_string(self.filename)
            except Exception as e:
                mess = 'Failed to format the filename: {}'
                traceback[err_path] = mess.format(e)
                return False, traceback

            full_path = os.path.join(full_folder_path, filename)

            overwrite = False
            if self.file_mode == 'New' and os.path.isfile(full_path):
                overwrite = True
                traceback[err_path + '-file'] = \
                    cleandoc('''File already exists, running the measure will
                    override it.''')

            try:
                f = open(full_path, 'ab')
                f.close()
                if self.file_mode == 'New' and not overwrite:
                    os.remove(full_path)
            except Exception as e:
                mess = 'Failed to open the specified file : {}'.format(e)
                traceback[err_path] = mess.format(e)
                return False, traceback

            try:
                self.format_string(self.header)
            except Exception as e:
                mess = 'Failed to format the header: {}'
                traceback[err_path] = mess.format(e)
                return False, traceback

        if self.array_size:
            try:
                self.format_and_eval_string(self.array_size)
            except Exception as e:
                mess = 'Failed to compute the array size: {}'
                traceback[err_path] = mess.format(e)
                return False, traceback

        elif self.saving_target != 'File':
            traceback[err_path] = 'A size for the array must be provided.'
            return False, traceback

        test = True
        for i, s in enumerate(self.saved_values):
            try:
                self.format_and_eval_string(s[1])
            except Exception as e:
                traceback[err_path + '-entry' + str(i)] = \
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
        if new != 'File':
            self.task_database_entries = {'array': numpy.array([1.0])}
        else:
            self.task_database_entries = {}


class SaveFileTask(SimpleTask):
    """ Save the specified entries in a CSV file.

    Wait for any parallel operation before execution.

    Notes
    -----
    Currently only support saving floats and arrays of floats (record arrays
    or simple arrays).

    """
    #: Folder in which to save the data.
    folder = Unicode('{default_path}').tag(pref=True)

    #: Name of the file in which to write the data.
    filename = Unicode().tag(pref=True)

    #: Currently opened file object. (File mode)
    file_object = Value()

    #: Header to write at the top of the file.
    header = Str().tag(pref=True)

    #: List of values to be saved store as (label, value).
    saved_values = ContainerList(Tuple()).tag(pref=True)

    #: Flag indicating whether or not initialisation has been performed.
    initialized = Bool(False)

    #: Column indices identified as arrays.
    array_values = Value()

    task_database_entries = set_default({'file': None})

    wait = set_default({'activated': True})  # Wait on all pools by default.

    def perform(self):
        """ Collect all data and write them to file.

        """
        # Initialisation.
        if not self.initialized:

            full_folder_path = self.format_string(self.folder)
            filename = self.format_string(self.filename)
            full_path = os.path.join(full_folder_path, filename)
            try:
                self.file_object = open(full_path, 'wb')
            except IOError as e:
                log = logging.getLogger()
                mes = cleandoc('''In {}, failed to open the specified
                                file {}'''.format(self.task_name, e))
                log.error(mes)
                self.root_task.should_stop.set()

            self.root_task.files[full_path] = self.file_object

            if self.header:
                h = self.format_string(self.header)
                for line in h.split('\n'):
                    self.file_object.write('# ' + line + '\n')

            labels = []
            self.array_values = set()
            for i, s in enumerate(self.saved_values):
                value = self.format_and_eval_string(s[1])
                if isinstance(value, numpy.ndarray):
                    names = value.dtype.names
                    self.array_values.add(i)
                    if names:
                        labels.extend([s[0] + '_' + m for m in names])
                    else:
                        labels.append(s[0])
                else:
                    labels.append(s[0])
            self.file_object.write('\t'.join(labels) + '\n')
            self.file_object.flush()

            self.initialized = True

        lengths = set()
        values = []
        for i, s in enumerate(self.saved_values):
            value = self.format_and_eval_string(s[1])
            values.append(value)
            if i in self.array_values:
                lengths.add(value.shape[0])
                if len(value.shape) > 1:
                    log = logging.getLogger()
                    mes = cleandoc('''In {}, impossible to save arrays exceeding
                                    one dimension. Save file in HDF5 format. 
                                    '''.format(self.task_name))
                    log.error(mes)
                    self.root_task.should_stop.set()

        if lengths:
            if len(lengths) > 1:
                log = logging.getLogger()
                mes = cleandoc('''In {}, impossible to save simultaneously
                                arrays of different sizes.
                                Save file in HDF5 format. 
                                '''.format(self.task_name))
                log.error(mes)
                self.root_task.should_stop.set()
            else:
                length = lengths.pop()

        if not self.array_values:
            self.file_object.write('\t'.join([str(val) for val in values]) +
                                   '\n')
            self.file_object.flush()
        else:
            columns = []
            for i, val in enumerate(values):
                if i in self.array_values:
                    if val.dtype.names:
                        columns.extend([val[m] for m in val.dtype.names])
                    else:
                        columns.append(val)
                else:
                    columns.append(numpy.ones(length)*val)
            array_to_save = numpy.rec.fromarrays(columns)
            numpy.savetxt(self.file_object, array_to_save, delimiter='\t')
            self.file_object.flush()

    def check(self, *args, **kwargs):
        """
        """
        err_path = self.task_path + '/' + self.task_name
        traceback = {}
        try:
            full_folder_path = self.format_string(self.folder)
        except Exception as e:
            mess = 'Failed to format the folder path: {}'
            traceback[err_path] = mess.format(e)
            return False, traceback

        try:
            filename = self.format_string(self.filename)
        except Exception as e:
            mess = 'Failed to format the filename: {}'
            traceback[err_path] = mess.format(e)
            return False, traceback

        full_path = os.path.join(full_folder_path, filename)

        overwrite = False
        if os.path.isfile(full_path):
            overwrite = True
            traceback[err_path + '-file'] = \
                cleandoc('''File already exists, running the measure will
                override it.''')

        try:
            f = open(full_path, 'ab')
            f.close()
            if not overwrite:
                os.remove(full_path)
        except Exception as e:
            mess = 'Failed to open the specified file : {}'.format(e)
            traceback[err_path] = mess.format(e)
            return False, traceback

        try:
            self.format_string(self.header)
        except Exception as e:
            mess = 'Failed to format the header: {}'
            traceback[err_path] = mess.format(e)
            return False, traceback

        test = True
        for i, s in enumerate(self.saved_values):
            try:
                self.format_and_eval_string(s[1])
            except Exception as e:
                traceback[err_path + '-entry' + str(i)] = \
                    'Failed to evaluate entry {}: {}'.format(s[0], e)
                test = False

        return test, traceback
        
class _HDF5File(h5py.File):
    """ 
        Resize the datasets before closing the file
        Sets the compression with a boolean
    """

    def close(self):
        for dataset in self.keys():
            oldshape = self[dataset].shape
            newshape = (self.attrs['countCalls'], ) + oldshape[1:]
            self[dataset].resize(newshape)
        super(_HDF5File, self).close()

    def create_dataset(self, name, shape, maximumshape, datatype, compress):
        f = super(_HDF5File, self)
        if compress:
            f.create_dataset(name, shape, maxshape=maximumshape, dtype=datatype, compression='gzip')
        else:
            f.create_dataset(name, shape, maxshape=maximumshape, dtype=datatype)
            

class SaveFileHDF5Task(SimpleTask):
    """ Save the specified entries in a HDF5 file.

    Wait for any parallel operation before execution.

    """
    #: Folder in which to save the data.
    folder = Unicode('{default_path}').tag(pref=True)

    #: Name of the file in which to write the data.
    filename = Unicode().tag(pref=True)

    #: Currently opened file object. (File mode)
    file_object = Value()

    #: Header to write at the top of the file.
    header = Str().tag(pref=True)

    #: List of values to be saved store as (label, value).
    saved_values = ContainerList(Tuple()).tag(pref=True)
    
    #: data type (float16, float32, etc.)
    datatype = Enum('float16', 'float32', 'float64').tag(pref=True)
    
    #: gzip compression of the data in the HDF5 file
    compression = Bool(False).tag(pref=True)

    #: estimation of the number of calls of this task during the measure. This helps h5py to chunk the file appropriately
    callsEstimation = Str('1').tag(pref=True)

    #: Flag indicating whether or not initialisation has been performed.
    initialized = Bool(False)

    task_database_entries = set_default({'file': None})

    wait = set_default({'activated': True})  # Wait on all pools by default.

    def perform(self):
        """ Collect all data and write them to file.

        """

        callsEstimation = self.format_and_eval_string(self.callsEstimation)        
        
        # Initialisation.
        if not self.initialized:

            full_folder_path = self.format_string(self.folder)
            filename = self.format_string(self.filename)
            full_path = os.path.join(full_folder_path, filename)
            try:
                self.file_object = _HDF5File(full_path, 'w')
            except IOError as e:
                log = logging.getLogger()
                mes = cleandoc('''In {}, failed to open the specified
                                file {}'''.format(self.task_name, e))
                log.error(mes)
                self.root_task.should_stop.set()

            self.root_task.files[full_path] = self.file_object

            f = self.file_object
            for s in self.saved_values:
                value = self.format_and_eval_string(s[1])
                if isinstance(value, numpy.ndarray):
                    names = value.dtype.names
                    if names:
                        for m in names:
                            f.create_dataset(s[0] + '_' + m, 
                                             (callsEstimation, ) + value.shape,
                                             (None, ) + value.shape,
                                             self.format_string(self.datatype),
                                             self.compression )
                    else:
                        f.create_dataset(s[0], 
                                         (callsEstimation, ) + value.shape,
                                         (None, ) + value.shape,
                                         self.format_string(self.datatype),
                                         self.compression )
                else:
                    f.create_dataset(s[0], (callsEstimation, ), (None, ), self.format_string(self.datatype), self.compression)
            f.attrs['header'] = self.format_string(self.header)
            f.attrs['countCalls'] = 0
            f.flush()

            self.initialized = True
        
        f = self.file_object
        countCalls = f.attrs['countCalls']
        
        if not (countCalls % callsEstimation):
            for dataset in f.keys():
                oldshape = f[dataset].shape
                newshape = (oldshape[0] + callsEstimation, ) + oldshape[1:]
                f[dataset].resize(newshape)
        
        for s in self.saved_values:
            value = self.format_and_eval_string(s[1])
            if isinstance(value, numpy.ndarray):
                names = value.dtype.names
                if names:
                    for m in names:
                        f[s[0] + '_' + m][countCalls] = value[m]
                else:
                    f[s[0]][countCalls] = value
            else:
                f[s[0]][countCalls] = value
                
        f.attrs['countCalls'] = countCalls + 1
        f.flush()

    def check(self, *args, **kwargs):
        """
        """
        err_path = self.task_path + '/' + self.task_name
        traceback = {}
        try:
            full_folder_path = self.format_string(self.folder)
        except Exception as e:
            mess = 'Failed to format the folder path: {}'
            traceback[err_path] = mess.format(e)
            return False, traceback

        try:
            filename = self.format_string(self.filename)
        except Exception as e:
            mess = 'Failed to format the filename: {}'
            traceback[err_path] = mess.format(e)
            return False, traceback

        full_path = os.path.join(full_folder_path, filename)

        overwrite = False
        if os.path.isfile(full_path):
            overwrite = True
            traceback[err_path + '-file'] = \
                cleandoc('''File already exists, running the measure will
                override it.''')

        try:
            f = open(full_path, 'ab')
            f.close()
            if not overwrite:
                os.remove(full_path)
        except Exception as e:
            mess = 'Failed to open the specified file : {}'.format(e)
            traceback[err_path] = mess.format(e)
            return False, traceback

        try:
            self.format_string(self.header)
        except Exception as e:
            mess = 'Failed to format the header: {}'
            traceback[err_path] = mess.format(e)
            return False, traceback
        
        values_name = [s[0] for s in self.saved_values]
        if len(values_name) != len(set(values_name)):
            traceback[err_path] = \
                    cleandoc('''All labels must be different.''')
            return False, traceback
            
        test = True
        for i, s in enumerate(self.saved_values):
            try:
                self.format_and_eval_string(s[1])
            except Exception as e:
                traceback[err_path + '-entry' + str(i)] = \
                    'Failed to evaluate entry {}: {}'.format(s[0], e)
                test = False            
        return test, traceback


class SaveArrayTask(SimpleTask):
    """Save the specified array either in a CSV file or as a .npy binary file.

    Wait for any parallel operation before execution.

    """

    #: Folder in which to save the data.
    folder = Unicode().tag(pref=True)

    #: Name of the file in which to write the data.
    filename = Str().tag(pref=True)

    #: Header to write at the top of the file.
    header = Str().tag(pref=True)

    #: Name of the array to save in the database.
    target_array = Str().tag(pref=True)

    #: Flag indicating whether to save as csv or .npy.
    mode = Enum('Text file', 'Binary file').tag(pref=True)

    wait = set_default({'activated': True})  # Wait on all pools by default.

    def perform(self):
        """ Save array to file.

        """
        array_to_save = self.format_and_eval_string(self.target_array)

        assert isinstance(array_to_save, numpy.ndarray), 'Wrong type returned.'

        full_folder_path = self.format_string(self.folder)

        filename = self.format_string(self.filename)

        full_path = os.path.join(full_folder_path, filename)

        # Create folder if it does not exists.
        try:
            os.makedirs(full_folder_path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

        if self.mode == 'Text file':
            try:
                file_object = open(full_path, 'wb')
            except IOError:
                mes = cleandoc('''In {}, failed to open the specified
                                file'''.format(self.task_name))
                log = logging.getLogger()
                log.error(mes)
                raise

            if self.header:
                h = self.format_string(self.header)
                for line in h.split('\n'):
                    file_object.write('# ' + line + '\n')

            if array_to_save.dtype.names:
                file_object.write('\t'.join(array_to_save.dtype.names) + '\n')

            numpy.savetxt(file_object, array_to_save, delimiter='\t')
            file_object.close()

        else:
            try:
                file_object = open(full_path, 'wb')
                file_object.close()
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
        err_path = self.task_path + '/' + self.task_name
        try:
            full_folder_path = self.format_string(self.folder)
        except Exception as e:
            traceback[err_path] = \
                'Failed to format the folder path: {}'.format(e)
            return False, traceback

        if self.mode == 'Binary file':
            if len(self.filename) > 3 and self.filename[-4] == '.'\
                    and self.filename[-3:] != 'npy':
                self.filename = self.filename[:-4] + '.npy'
                mes = cleandoc("""The extension of the file will be
                                replaced by '.npy' in task
                                {}""".format(self.task_name))
                traceback[err_path + '-file_ext'] = mes

            if self.header:
                traceback[err_path + '-header'] =\
                    'Cannot write a header when saving in binary mode.'

        try:
            filename = self.format_string(self.filename)
        except Exception as e:
            traceback[err_path] = \
                'Failed to format the filename: {}'.format(e)
            return False, traceback

        full_path = os.path.join(full_folder_path, filename)

        overwrite = False
        if os.path.isfile(full_path):
            overwrite = True
            traceback[err_path + '-file'] = \
                cleandoc('''File already exists, running the measure will
                override it.''')

        try:
            f = open(full_path, 'ab')
            f.close()
            if not overwrite:
                os.remove(full_path)
        except Exception as e:
            mess = 'Failed to open the specified file: {}'
            traceback[err_path] = mess.format(e)
            return False, traceback

        try:
            self.format_string(self.header)
        except Exception as e:
            mess = 'Failed to format the header: {}'
            traceback[err_path] = mess.format(e)
            return False, traceback

        try:
            array = self.format_and_eval_string(self.target_array)
        except Exception as e:
            traceback[err_path] = \
                'Failed to evaluate target_array : {}'.format(e)
            return False, traceback

        if not isinstance(array, numpy.ndarray):
            traceback[err_path] = \
                'Target array evaluation did not return an array'
            return False, traceback

        return True, traceback

KNOWN_PY_TASKS = [SaveTask, SaveFileTask, SaveFileHDF5Task, SaveArrayTask]
