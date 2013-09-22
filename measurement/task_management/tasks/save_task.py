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
    """
    """

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
            directory = dlg.selectedFiles()[0]
            info.object.folder = directory

    def object_fill_header_changed(self, info):
        """
        """
        task = info.object
        task.edit_traits(view = 'header_view',
                                parent = info.ui.control,
                                kind = 'livemodal')

class SaveTask(SimpleTask):
    """
    """
    folder = Str('', preference = True)
    filename = Str('', preference = True)
    file_object = Any
    csv_writer = Any #Instance(csv.writer)
    header = Str('', preference = True)
    fill_header = Button('Edit')

    array = Array

    saving_target = Enum('File', 'Array', 'File and array', preference = True)

    array_size = Str(preference = True)
    array_length = Int
    line_index = Int(0)

    saved_labels = List(Str, preference = True)
    saved_values = List(Str, preference = True)
    saved_objects = List(Instance(SavedValueObject))

    initialized = Bool(False)
    database_entries = ['array', 'file']
    accessible_entries = List(Str)
    explore_button = Button('Browse')

    #task_view = View()
    header_view = View(UItem('header@'), buttons = ['OK', 'Cancel'])

    def __init__(self, *args, **kwargs):
        super(SaveTask, self).__init__(*args, **kwargs)
        self._define_task_view()
        self.on_trait_change(name = 'saved_objects:[label, value]',
                             handler = self._saved_objects_modified)

    @make_stoppable
    @make_wait
    def process(self):
        """
        """
        #Init
        if not self.initialized:
            if self.saving_target != 'Array':
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
                    return
                self.csv_writer = csv.writer(self.file_object, delimiter = '\t')
                self.write_in_database('file', self.file_object)
                self.csv_writer.writerow(self.saved_labels)

            if self.saving_target != 'File':
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

        #writing
        values = [eval(get_formatted_string(value,
                                       self.task_path,
                                       self.task_database))
                    for value in self.saved_values]
        if self.saving_target != 'Array':
            self.csv_writer.writerow(values)
        if self.saving_target != 'File':
            self.array[self.line_index] = tuple(values)

        self.line_index += 1

        #Closing
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
            print 'In {}, failed to open the specified file'.format(
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

        try:
            [eval(get_formatted_string(value,
                                       self.task_path,
                                       self.task_database))
                    for value in self.saved_values]
        except:
            print 'In {}, failed to evaluate one of the entries'.format(
                                                            self.task_name)
            return False

        return True

    def update_preferences_from_traits(self):
        """
        """
        self._saved_objects_modified()
        for name in self.traits(preference = True):
            self.task_preferences[name] = str(self.get(name).values()[0])

    def update_traits_from_preferences(self, **parameters):
        """
        """
        super(SaveTask, self).update_traits_from_preferences(**parameters)
        self.on_trait_change(name = 'saved_objects:[label, value]',
                             handler = self._saved_objects_modified,
                             remove = True)
        for i, label in enumerate(self.saved_labels):
            self.saved_objects.append(
                    SavedValueObject(label = label,
                                     value = self.saved_values[i]))
        self.on_trait_change(name = 'saved_objects:[label, value]',
                             handler = self._saved_objects_modified)

    def _saved_objects_modified(self):
        """
        """
        self.saved_labels = [obj.label for obj in self.saved_objects]
        self.saved_values = [obj.value for obj in self.saved_objects]

    def _update_database_entries(self):
        """
        """
        self.accessible_entries = \
                    self.task_database.list_accessible_entries(self.task_path)
        return self.accessible_entries

    def _define_task_view(self):
        """
        """
        line_completer = LineCompleterEditor(
                             entries_updater = self._update_database_entries)
        label_col = ObjectColumn(name = 'label',
                         label = 'Label',
                         horizontal_alignment = 'center',
                         width = 0.4,
                         )
        value_col = ObjectColumn(name = 'value',
                         label = 'Value',
                         horizontal_alignment = 'center',
                         editor = line_completer,
                         width = 0.6,
                         )
        table_editor = TableEditor(
                editable  = True,
                sortable  = False,
                auto_size = False,
                reorderable = True,
                deletable = True,
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
                            UItem('filename', springy = True),
                            label = 'Filename',
                            show_border = True,
                            ),
                        HGroup(
                            UItem('fill_header'),
                            label = 'Header',
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