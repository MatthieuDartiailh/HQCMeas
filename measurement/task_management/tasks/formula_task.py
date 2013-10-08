# -*- coding: utf-8 -*-
"""
"""
from traits.api import (Str, List, Instance, HasTraits, Bool)
from traitsui.api import (View, UItem, VGroup, LineCompleterEditor, TableEditor,
                        ObjectColumn, TextEditor)

from math import (cos, sin, tan, acos, asin, atan,
                exp, log, cosh, sinh, tanh)
from math import pi as Pi

from .base_tasks import SimpleTask
from .tools.database_string_formatter import (get_formatted_string,
                                              format_and_eval_string)
from .tools.task_decorator import make_stoppable, make_wait

class FormulaObject(HasTraits):
    """
    """
    label = Str
    formula = Str

class FormulaTask(SimpleTask):
    """
    """
    labels = List(Str, preference = True)
    formulas = List(Str, preference = True)
    objects = List(Instance(FormulaObject))
    database_ready = Bool(False)

    def __init__(self, *args, **kwargs):
        super(FormulaTask, self).__init__(*args, **kwargs)
        self._define_task_view()
        self.on_trait_change(name = 'objects:[label, formula]',
                            handler = self._objects_modified)

    @make_stoppable
    @make_wait
    def process(self):
        """
        """
        for i, label in enumerate(self.labels):
            value = format_and_eval_string(self.formulas[i],
                                                self.task_path,
                                                self.task_database)
            self.write_in_database(label, value)

    def check(self, *args, **kwargs):
        """
        """
        traceback = {}
        for i, formula in enumerate(self.formulas):
            try:
                for_str = get_formatted_string(formula,
                                           self.task_path,
                                           self.task_database)
            except:
                traceback[self.task_path + '/' +self.task_name + str(i)] =\
                    "Failed to format the formula {}".format(
                                            self.labels[i])
                return False, traceback
            try:
                self.write_in_database(self.labels[i], eval(for_str))
            except:
                traceback[self.task_path + '/' +self.task_name + str(-i)] =\
                    "Failed to eval the formula {}".format(
                                            self.labels[i])
                return False, traceback
        return True, traceback

    def register_in_database(self):
        """
        """
        if not self.database_ready:
            self.database_ready = True
            self.on_trait_change(name = 'labels[]',
                            handler = self._labels_modified)
        self.task_database_entries = self.labels
        super(FormulaTask, self).register_in_database()

    def update_traits_from_preferences(self, **preferences):
        """
        """
        super(FormulaTask, self). update_traits_from_preferences(**preferences)
        self.on_trait_change(name = 'objects:[label, formula]',
                            handler = self._objects_modified,
                            remove = True)
        self.objects = [FormulaObject(label = self.labels[i],
                                      formula = self.formulas[i])
                        for i in xrange(len(self.labels))]
        self.on_trait_change(name = 'objects:[label, formula]',
                            handler = self._objects_modified)

    #@on_trait_change('objects:[label, formula]')
    def _objects_modified(self):
        """
        """
        self.labels = [obj.label for obj in self.objects]
        self.formulas = [obj.formula for obj in self.objects]

    #@on_trait_change('labels[]')
    def _labels_modified(self, obj, name, old, new):
        """
        """
        added = set(new) - set(old)
        removed = set(old) - set(new)
        for label in removed:
            self.task_database_entries.remove(label)
#            self.remove_from_database(self.task_name + '_' + label)
        for label in added:
            self.task_database_entries.append(label)
#            self.write_in_database(label, None)

    def _list_database_entries(self):
        """
        """
        return self.task_database.list_accessible_entries(self.task_path)

    def _define_task_view(self):
        label_col = ObjectColumn(
                    name = 'label',
                    label = 'Label',
                    horizontal_alignment = 'center',
                    editor = TextEditor(auto_set = False, enter_set = True),
                    width = 0.3,
                    auto_editable = True,
                    )
        formula_col = ObjectColumn(
                    name = 'formula',
                    label = 'Formula',
                    horizontal_alignment = 'center',
                    editor = LineCompleterEditor(
                        entries_updater = self._list_database_entries),
                    width = 0.7,
                    )
        table_ed = TableEditor(
            deletable = True,
            reorderable = True,
            auto_size = False,
            sortable = False,
            edit_on_first_click = True,
            selection_mode = 'cell',
            row_factory = FormulaObject,
            columns = [label_col,
                        formula_col],
            )
        view = View(
                VGroup(
                    UItem('task_name', style = 'readonly'),
                    VGroup(
                        UItem('objects',
                            editor = table_ed,
                            ),
                        show_border = True,
                        ),
                    ),
                resizable = True,
                )
        self.trait_view('task_view', view)