# -*- coding: utf-8 -*-
"""
"""
from traits.api import (Str, Float, List, Instance, HasTraits)
from traitsui.api import (View, Group, UItem, Label, HGroup,
                          LineCompleterEditor, ObjectColumn, TableEditor,
                          VGroup)
from time import sleep
from inspect import cleandoc

from .base_tasks import SimpleTask
from .tools.task_decorator import make_stoppable, make_wait
from .tools.database_string_formatter import get_formatted_string, safe_eval

class PrintTask(SimpleTask):
    """Basic task which simply prints a message in stdout. Loopable.
    """

    loopable = True
    task_database_entries = {'message' : ''}
    message = Str('', preference = True)

    def __init__(self, *args, **kwargs):
        super(PrintTask, self).__init__(*args, **kwargs)
        self._define_task_view()

    @make_stoppable
    def process(self, *args, **kwargs):
        """
        """
        mess = get_formatted_string(self.message,
                                    self.task_path,
                                    self.task_database)
        self.write_in_database('message', mess)
        print mess

    def check(self, *args, **kwargs):
        """
        """
        mess = get_formatted_string(self.message,
                                    self.task_path,
                                    self.task_database)
        self.write_in_database('message', mess)
        return True, {}

    def _list_database_entries(self):
        """
        """
        return self.task_database.list_accessible_entries(self.task_path)

    def _define_task_view(self):
        """
        """
        task_view = View(
                    Group(
                        UItem('task_name', style = 'readonly'),
                        HGroup(
                            Label('Message'),
                            UItem('message', springy = True,
                                  editor = LineCompleterEditor(
                              entries_updater = self._list_database_entries)
                              ),
                            show_border = True,
                            ),
                        ),
                    )
        self.trait_view('task_view', task_view)

class SleepTask(SimpleTask):
    """Simply sleeps for the specified amount of time. Wait for any parallel
    operation before execution.
    """

    time = Float(preference = True)
    task_view = View(
                    Group(
                        UItem('task_name', style = 'readonly'),
                        HGroup(
                            Label('Time to sleep (s)'),
                            UItem('time'),
                            show_border = True,
                            ),
                        ),
                    )

    @make_stoppable
    @make_wait()
    def process(self):
        """
        """
        sleep(self.time)

    def check(self, *args, **kwargs):
        """
        """
        return True, {}

class DefinitionValueObject(HasTraits):
    """
    """

    label = Str
    value = Str

class DefinitionTask(SimpleTask):
    """Add static values in the database.
    """

    definition_labels = List(Str, preference = True)
    definition_values = List(Str, preference = True)
    definition_objects = List(Instance(DefinitionValueObject))

    def __init__(self, *args, **kwargs):
        super(DefinitionTask, self).__init__(*args, **kwargs)
        self._define_task_view()
        self.on_trait_change(name = 'definition_objects.[label, value]',
                             handler = self._definition_objects_modified)

    @make_stoppable
    def process(self):
        """
        """
        return

    def check(self, *args, **kwargs):
        """
        """
        test = True
        traceback = {}

        for i, entry in enumerate(self.definition_labels):
            try:
                val = safe_eval(self.definition_values[i])
                self.write_in_database(entry, val)
            except:
                test = False
                traceback[self.task_path + '/' + self.task_name + '-' + entry] \
                    = cleandoc('''Failed to eval definition {}
                            '''.format(self.definition_values[i]))
        return test, traceback

    def update_preferences_from_traits(self):
        """
        """
        self._definition_objects_modified()
        for name in self.traits(preference = True):
            self.task_preferences[name] = str(self.get(name).values()[0])

    def update_traits_from_preferences(self, **parameters):
        """
        """
        super(DefinitionTask, self).update_traits_from_preferences(**parameters)
        self.on_trait_change(name = 'definition_objects.[label, value]',
                             handler = self._definition_objects_modified,
                             remove = True)
        for i, label in enumerate(self.definition_labels):
            self.definition_objects.append(
                    DefinitionValueObject(label = label,
                                     value = self.definition_values[i]))
        self.on_trait_change(name = 'definition_objects.[label, value]',
                             handler = self._definition_objects_modified)
        self._definition_objects_modified()

    def _definition_objects_modified(self):
        """
        """
        self.definition_labels = [obj.label for obj in self.definition_objects]
        self.definition_values = [obj.value for obj in self.definition_objects]
        self.task_database_entries = {obj.label : obj.value
                                        for obj in self.definition_objects}

    def _define_task_view(self):
        """
        """
        label_col = ObjectColumn(name = 'label',
                         label = 'Label',
                         horizontal_alignment = 'center',
                         width = 0.4,
                         )
        value_col = ObjectColumn(name = 'value',
                         label = 'Value',
                         horizontal_alignment = 'center',
                         width = 0.6,
                         )
        table_editor = TableEditor(
                editable  = True,
                sortable  = False,
                auto_size = False,
                reorderable = True,
                deletable = True,
                row_factory = DefinitionValueObject,
                columns = [label_col,
                            value_col],
                )
        view = View(
                UItem('task_name', style = 'readonly'),
                VGroup(
                    UItem('definition_objects',
                        editor = table_editor,
                        ),
                    show_border = True,
                    ),
                resizable = True,
                )
        self.trait_view('task_view', view)
