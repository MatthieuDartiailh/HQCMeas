# -*- coding: utf-8 -*-
"""
"""
from traits.api\
    import (HasTraits, Str, Int, Instance, List, Float, Bool, Property,
            on_trait_change)
from traitsui.api\
     import (View, ListInstanceEditor, VGroup, HGroup, Spring, UItem)

from config_obj import Section#, ConfigObj
from visa import Instrument
from numpy import linspace

from task_database import TaskDatabase

class AbstractTask(HasTraits):
    """Abstract  class defining common traits of all Task

    This class basically defines the minimal skeleton of a Task in term of
    traits and methods.
    """
    task_name = Str('')
    task_depth = Int(0)
    task_preferences = Instance(Section)
    task_database = Instance(TaskDatabase)
    task_database_entries = Instance(Str)
    task_path = Str('')
    #task_root = Instance(RootTask)

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

class SimpleTask(AbstractTask):
    """Convenience class for simple task ie task with no child task.
    """
    task_view = View
    loopable = Bool(False)

class InstrumentTask(SimpleTask):
    """Class for simple task involving the use of an instrument.
    """
    instr = Instance(Instrument)

class ComplexTask(AbstractTask):
    """
    """
    children_task = List(Instance(AbstractTask))
    task_view = Property(Instance(View))

    #won't do a lot save calling root
    def create_child(self):
        """Method to handle the adding of a child through the list editor
        """
        child = self.root_task.request_child(parent = self)
        return child

#    #likely useless
#    def remove_child(self):
#        """Method to handle the removing of a child through the list editor
#        """
#        pass

    def check(self):
        """Implementation of the test method of AbstractTask
        """
        test = True
        for child in self.children_task:
            test = test and child.check()
        return test

    #TODO must answer all modification resulting from an update cause by the parent
    @on_trait_change('task_name, task_path')
    def update_paths(self, obj, name, new, old):
        """Method taking care that the path of children, the database and the
        task name remains coherent
        """
        if name == 'task_name':
            self.task_database.rename_node(self.task_path, new, old)
            for child in self.children_task:
                child.task_path = self.task_path + new
        if name == 'task_path':
            for child in self.children_task:
                child.task_path = new + self.task_name

    @on_trait_change('children_task[]')
    def on_children_modified(self, obj, name, new, old):
        """Handle children being added or removed from the task, no matter the
        source"""
        if new and old:
            inter = set(new).intersection(old)
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
        child.depth = self.depth + 1
        self.preferences[child.task_name] = child.task_preferences
        child.task_path = self.task_path + self.task_name
        child.register_in_database()

    def _child_removed(self, child):
        """Method updating the database and preference tree when a child is
        removed
        """
        del self.preferences[child.task_name]
        entries = child.task_database_entries
        for entry in entries:
            self.task_database.delete_value(self.task_path + self.task_name,
                                            entry)

    def _get_task_view(self):
        return View(
                VGroup(
                    UItem('task_name'),
                    HGroup(
                        Spring(width = 40, springy = False),
                        UItem('children_task@',
                              editor = ListInstanceEditor()),
                        ),
                    )
                )


class LoopTask(ComplexTask):
    """
    """
    task = Instance(SimpleTask)
    task_start = Float(0.0)
    task_stop = Float(1.0)
    task_step = Float(0.1)

    def perform(self):
        """
        """
        num = int((self.task_stop - self.task_start)/self.task_step) + 1
        for value in linspace(self.task_start, self.task_stop, num):
            self.task.process(value)
            for child in self.children_task:
                child.perform()

    def _get_task_view(self):
        return View(
                    VGroup(
                        HGroup(
                            UItem('task_name'),
                            UItem('task_start'),
                            UItem('task_stop'),
                            UItem('task_step'),
                            UItem('task'),
                            ),
                        HGroup(
                            Spring(width = 40, springy = False),
                            UItem('children_task@',
                                  editor = ListInstanceEditor()),
                            ),
                        )
                    )



class RootTask(ComplexTask):
    """Special task which is always the root of a measurement and is the only
    task directly referencing the measurement editor.
    """
    measurement_editor = Instance

