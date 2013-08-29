# -*- coding: utf-8 -*-
"""
"""

from traits.api import (Instance, Array, List, Str, Enum, Any, HasTraits,
                        Button, Bool, Int)
from traitsui.api import (View, HGroup, VGroup, UItem, ObjectColumn, Handler,
                          TableEditor, Label, LineCompleterEditor)
from pyface.qt import QtGui

import csv, os, numpy

from .tools.database_string_formatter import get_formatted_string
from .tools.task_decorator import make_stoppable, make_wait
from .base_tasks import SimpleTask

class SavedValueObject(HasTraits):

    label = Str
    value = Str

class SaveTaskHandler(Handler):
    """
    """
    def object_explore_button_changed(self, info):
        """
        """
        dlg = QtGui.QFileDialog(info.ui.control)
        dlg.setFileMode(QtGui.QFileDialog.Directory)
        if dlg.exec_() == QtGui.QDialog.Accepted:
            dir = dlg.selectedFiles()
            self.folder = dir

class SaveTask(SimpleTask):
    """
    """
    folder = Str('', preference = True)
    filename = Str('', preference = True)
    file_object = Any
    csv_writer = Instance(csv.writer)

    array_size = Str
    array_length = Int
    array = Array
    line_index = Int(0)

    saving_target = Enum('File', 'Array', 'File and array', preference = True)

    saved_labels = List(Str, preference = True)
    saved_values = List(Str, preference = True)
    saved_objects = List(Instance(SavedValueObject))

    initialized = Bool(False)
    database_entries = ['array', 'file']
    explore_button = Button('Browse')

    #task_view = View()

    def __init__(self, *args, **kwargs):
        super(SaveTask, self).__init__(*args, **kwargs)
        self._define_task_view()

    @make_stoppable
    @make_wait
    def process(self):
        """
        """
        if not self.initialized:
            full_folder_path = get_formatted_string(self.folder,
                                                     self.task_path,
                                                     self.task_database)
            full_path = os.path.join(full_folder_path, self.filename)
            try:
                self.file_object = open(full_path, 'wb')
            except IOError:
                print 'In {}, to open the specified file'.format(
                                                            self.task_name)
                self.root_task.should_stop.set()
            self.csv_writer = csv.writer(self.file_object, delimiter = '\t')
            self.write_in_database('file', self.file_object)
            self.array_length = eval(get_formatted_string(self.array_size,
                                                           self.task_path,
                                                           self.task_database))
            array_type = numpy.dtype([(name, 'f8')
                                        for name in self.saved_labels])
            self.array = numpy.empty((self.array_length,
                                      len(self.saved_labels)),
                                     dtype = array_type)
            self.write_in_database('array', self.array)
            self.initialized = True

        #do stuff

        self.line_index += 1
        if self.line_index == self.array_length:
            self.file_object.close()
            self.initialized = False

    def check(self, *args, **kwargs):
        """
        """
        try:
            full_folder_path = get_formatted_string(self.folder,
                                                         self.task_path,
                                                         self.task_database)
        except:
            print 'In {}, failed to format the folder path'.format(
                                                            self.task_name)
            return False

        full_path = os.path.join(full_folder_path, self.filename)

        try:
            f = open(full_path, 'wb')
            f.close()
        except:
            print 'In {}, to open the specified file'.format(
                                                            self.task_name)
            return False

        try:
            eval(get_formatted_string(self.array_size,
                                       self.task_path,
                                       self.task_database))
        except:
            print 'In {}, failed to compute the array size'.format(
                                                            self.task_name)
            return False

        return True

    def update_trais_from_preferences(self, **parameters):
        """
        """
        super(SaveTask, self).update_traits_from_preferences(**parameters)
        self.on_trait_change(name = 'saved_objects',
                             handler = self._saved_objects_modified,
                             remove = True)
        for i, label in enumerate(self.saved_labels):
            self.saved_object.append(
                    SavedValueObject(label = label,
                                     value = self.saved_values[i]))
        self.on_trait_change(name = 'saved_objects',
                             handler = self._saved_objects_modified)

    def _saved_objects_modified(self):
        """
        """
        self.saved_labels = [obj.label for obj in self.saved_objects]
        self.saved_values = [obj.value for obj in self.saved_objects]

    def _update_database_entries(self):
        """
        """
        return self.task_database.list_accessible_entries(self.path)

    def _define_task_view(self):
        """
        """
        line_completer = LineCompleterEditor(
                             entries_updater = self._update_database_entries)
        label_col = ObjectColumn(name = 'label',
                         label = 'Label',
                         horizontal_alignment = 'center',
                         )
        value_col = ObjectColumn(name = 'value',
                         label = 'Value',
                         horizontal_alignment = 'center',
                         editor = line_completer
                         )
        table_editor = TableEditor(
                editable  = True,
                sortable  = False,
                auto_size = False,
                reorderable = True,
                deletable = True,
                show_toolbar = True,
                row_factory = SavedValueObject,
                columns = [label_col,
                            value_col],
                )
        view = View(
                UItem('task_name', style = 'readonly'),
                VGroup(
                    HGroup(
                        Label('Save to :'),
                        UItem('saving_target'),
                        ),
                    HGroup(
                        Label('# of points'),
                        UItem('array_size',
                            editor = line_completer,
                            tooltip = "Enter the number of points to be saved",
                            ),
                        ),
                    HGroup(
                        HGroup(
                            UItem('folder',
                                editor = line_completer,
                                ),
                            UItem('explore_button'),
                            label = 'Folder',
                            show_border = True,
                            ),
                        HGroup(
                            UItem('filename'),
                            label = 'Filename',
                            show_border = True,
                            ),
                    enabled_when = "saving_target != 'Array'"
                    ),
                    UItem('saved_objects',
                        editor = table_editor,
                        ),
                    show_border = True,
                    ),
                handler = SaveTaskHandler(),
                resizable = True,
                )
        self.trait_view('task_view', view)
