# -*- coding: utf-8 -*-
"""
"""
from traits.api\
    import (HasTraits, Str, Int, Instance, List, Float, Bool, on_trait_change)
from traits.api import self as trait_self
from traitsui.api\
     import (View, ListInstanceEditor, VGroup, HGroup, Spring, UItem,
             InstanceEditor)

from configobj import Section, ConfigObj
#from visa import Instrument
from dummy import Instrument, Measurement
from numpy import linspace

from task_database import TaskDatabase

#TODO add preference gestion
class AbstractTask(HasTraits):
    """Abstract  class defining common traits of all Task

    This class basically defines the minimal skeleton of a Task in term of
    traits and methods.
    """
    task_name = Str
    task_depth = Int
    task_preferences = Instance(Section)
    task_database = Instance(TaskDatabase)
    task_database_entries = List(Str)
    task_path = Str
    #root_task = Instance(RootTask)

    def process(self, *args, **kwargs):
        """The main method of any task as it is this one which is called when
        the measurement is performed
        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractTask. This method is called when the program requires the task\
        to be performed'
        raise NotImplementedError(err_str)

    def check(self):
        """Method used to check that everything is alright before starting a
        measurement
        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractTask. This method is called when the program requires the task\
        to check that all parameters are ok'
        raise NotImplementedError(err_str)

    def register_in_database(self):
        """Method used to create entries in the database
        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractTask. This method is called when the program requires the task\
        to create its entry in the database'
        raise NotImplementedError(err_str)

    def unregister_from_database(self):
        """Method used to delete entries from the database
        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractTask. This method is called when the program requires the task\
        to delete its entry from the database'
        raise NotImplementedError(err_str)

    @on_trait_change('task_preferences')
    def _register_preferences(self):
        """
        """
        for name in self.traits(preference = True):
            self.task_preferences[name] = str(self.get(name).values()[0])

class SimpleTask(AbstractTask):
    """Convenience class for simple task ie task with no child task.
    """
    task_view = View
    loopable = Bool(False)

    def write_in_database(self, name, value):
        """
        """
        full_name = self.task_name + '_' + name
        self.task_database.set_value(self.task_path, full_name, value)

    def register_in_database(self):
        """
        """
        if self.task_database_entries:
            for entry in self.task_database_entries:
                self.task_database.set_value(self.task_path,
                                             self.task_name + '_' + entry,
                                             None)
    def unregister_from_database(self):
        """
        """
        if self.task_database_entries:
            for entry in self.task_database_entries:
                self.task_database.delete_value(self.task_path,
                                               self.task_name + '_' + entry)

class InstrumentTask(SimpleTask):
    """Class for simple task involving the use of an instrument.
    """
    instr = Instance(Instrument)

class ComplexTask(AbstractTask):
    """
    """
    children_task = List(Instance(AbstractTask))

    def __init__(self, *args, **kwargs):
        super(ComplexTask, self).__init__(*args, **kwargs)

        self._define_view()

        self.on_trait_change(self.update_paths,
                             name = 'task_name, task_path, task_depth')

    def process(self):
        """
        """
        for child in self.children_task:
                child.process()

    def create_child(self):
        """Method to handle the adding of a child through the list editor
        """
        child = self.root_task.request_child(parent = self)
        return child

    def check(self):
        """Implementation of the test method of AbstractTask
        """
        test = True
        for child in self.children_task:
            test = test and child.check()
        return test

    def register_in_database(self):
        """
        """
        if self.task_database_entries:
            for entry in self.task_database_entries:
                self.task_database.set_value(self.task_path,
                                             self.task_name + '_' + entry,
                                             None)

        self.task_database.create_node(self.task_path, self.task_name)

        if self.children_task:
            for child in self.children_task:
                child.register_in_database()

    def unregister_from_database(self):
        """
        """
        if self.task_database_entries:
            for entry in self.task_database_entries:
                self.task_database.delete_value(self.task_path, entry)

        self.task_database.delete_node(self.task_path, self.task_name)

        if self.children_task:
            for child in self.children_task:
                child.unregister_from_database()


    #@on_trait_change('task_name, task_path, task_depth')
    def update_paths(self, obj, name, old, new):
        """Method taking care that the path of children, the database and the
        task name remains coherent
        """
        if name == 'task_name':
            self.task_database.rename_node(self.task_path, new, old)
            if self.children_task:
                for child in self.children_task:
                    child.task_path = self.task_path + new
        if name == 'task_path':
            if self.children_task:
                for child in self.children_task:
                    child.task_path = new + self.task_name
        if name == 'task_depth':
            if self.children_task:
                for child in self.children_task:
                    child.task_depth = new + 1

    @on_trait_change('children_task[]')
    def on_children_modified(self, obj, name, old, new):
        """Handle children being added or removed from the task, no matter the
        source"""
        if new and old:
            inter = set(new).symmetric_difference(old)
            if inter:
                for child in inter:
                    if child in new:
                        self._child_added(child)
                    else:
                        self._child_removed(child)
        elif new:
            for child in new:
                self._child_added(child)

        elif old:
            for child in old:
                self._child_removed(child)

    def _child_added(self, child):
        """Method updating the database, depth and preference tree when a child
        is added
        """
        child.task_depth = self.task_depth + 1
        child.task_database = self.task_database
        child.root_task = self.root_task

        self.task_preferences[child.task_name] = {}
        child.task_preferences = self.task_preferences[child.task_name]

        child.task_path = self.task_path + '/' + self.task_name
        child.register_in_database()

    def _child_removed(self, child):
        """Method updating the database and preference tree when a child is
        removed
        """
        del self.task_preferences[child.task_name]
        child.unregister_from_database()

    def _define_view(self):
        """
        """
        task_view = View(
                    VGroup(
                        UItem('task_name', style = 'readonly'),
                        HGroup(
#                            Spring(width = 40, springy = False),
                            UItem('children_task@',
                                  editor = ListInstanceEditor(
                                      style = 'custom',
                                      editor = InstanceEditor(view =
                                                              'task_view'),
                                      item_factory = self.create_child)),
                            show_border = True,
                            ),
                        ),
                    )

        self.trait_view('task_view', task_view)


class LoopTask(ComplexTask):
    """
    """
    task = Instance(SimpleTask)
    task_start = Float(0.0)
    task_stop = Float(1.0)
    task_step = Float(0.1)

    def __init__(self, task_class, *args, **kwargs):
        super(LoopTask, self).__init__(*args, **kwargs)
        self._init_task(task_class)

    def process(self):
        """
        """
        num = int((self.task_stop - self.task_start)/self.task_step) + 1
        for value in linspace(self.task_start, self.task_stop, num):
            self.task.process(value)
            for child in self.children_task:
                child.process()

    #TODO must find something nice
    def _init_task(self, task_class):
        self.task = task_class(task_database = self.task_database,
                               root_task = self.root_task)

    def _define_view(self):
        task_view = View(
                    UItem('task_name', style = 'readonly'),
                    VGroup(
                        HGroup(
                            UItem('task_start'),
                            UItem('task_stop'),
                            UItem('task_step'),
                            UItem('task'),
                            ),
                        UItem('children_task@',
                          editor = ListInstanceEditor(
                              style = 'custom',
                              editor = InstanceEditor(view = 'task_view'),
                              item_factory = self.create_child)),
                        show_border = True,
                        )
                    )
        self.trait_view('task_view', task_view)

class RootTask(ComplexTask):
    """Special task which is always the root of a measurement and is the only
    task directly referencing the measurement editor.
    """
    measurement_editor = Instance(Measurement)
    root_task = trait_self
    task_database = TaskDatabase()
    task_name = 'Root'
    task_preferences = ConfigObj()
    task_depth = 0
    task_path = 'root'

    def request_child(self, parent):
        child = self.measurement_editor.task_builder.build(parent = parent)
        return child

    def _child_added(self, child):
        """Method updating the database, depth and preference tree when a child
        is added
        """
        child.task_depth = self.task_depth + 1
        child.task_database = self.task_database
        child.root_task = self.root_task

        self.task_preferences[child.task_name] = {}
        child.task_preferences = self.task_preferences[child.task_name]

        child.task_path = self.task_path
        child.register_in_database()

    def _child_removed(self, child):
        """Method updating the database and preference tree when a child is
        removed
        """
        del self.task_preferences[child.task_name]

        entries = child.task_database_entries
        path = self.task_path
        for entry in entries:
            self.task_database.delete_value(path, entry)

AbstractTask.add_class_trait('root_task', Instance(RootTask))