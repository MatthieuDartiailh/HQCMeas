# -*- coding: utf-8 -*-
"""
"""

from traits.api\
    import (HasTraits, Str, Int, Instance, List, Float, Bool, Dict, Type,
            on_trait_change, Unicode)
from traits.api import self as trait_self
from traitsui.api\
     import (View, ListInstanceEditor, VGroup, HGroup, UItem,
             InstanceEditor, Group, Label)

from configobj import Section, ConfigObj
from visa import Instrument
from numpy import linspace

from .task_database import TaskDatabase

class AbstractTask(HasTraits):
    """Abstract  class defining common traits of all Task

    This class basically defines the minimal skeleton of a Task in term of
    traits and methods.
    """
    task_class = Str(preference = True)
    task_name = Str(preference = True)
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

    def register_preferences(self):
        """Method used to create entries in the preferences object
        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractTask. This method is called when the program requires the task\
        to create its entries in the preferences object'
        raise NotImplementedError(err_str)

    def update_preferences_from_traits(self):
        """Method used to update the entries in the preference object before
        saving
        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractTask. This method is called when the program requires the task\
        to update the entries in the preference object before saving'
        raise NotImplementedError(err_str)

    def update_traits_from_preferences(self, **parameters):
        """Method used to update the trait values using the info extracted from
        a config file.

        Parameters:
        ----------
        parameters : dict
        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractTask. This method is called when the program requires the task\
        to update update the trait values using the info extracted from\
        a config file.'
        raise NotImplementedError(err_str)

    def _task_class_default(self):
        return self.__class__.__name__


class SimpleTask(AbstractTask):
    """Task with no child task, written in pure Python.
    """
    #Class attribute specifying if instances of that class can be used in loop
    # Not a Trait because otherwise would not be a class attribute
    loopable = False

    def write_in_database(self, name, value):
        """This method build a task specific database entry from the task_name
        and the name arg and set the database entry to the value specified.
        """
        value_name = self.task_name + '_' + name
        return self.task_database.set_value(self.task_path, value_name, value)

    def get_from_database(self, full_name):
        """This method return the value under the database entry specified by
        the full name (ie task_name + '_' + entry, where task_name is the name
        of the task that wrote the value in the database).
        """
        return self.task_database.get_value(self.task_path, full_name)

    def register_in_database(self):
        """
        """
        if self.task_database_entries:
            for entry in self.task_database_entries:
                self.task_database.set_value(self.task_path,
                                             self.task_name + '_' + entry, None)

    def unregister_from_database(self):
        """
        """
        if self.task_database_entries:
            for entry in self.task_database_entries:
                self.task_database.delete_value(self.task_path,
                                                self.task_name + '_' + entry)

    def register_preferences(self):
        """
        """
        for name in self.traits(preference = True):
                self.task_preferences[name] = str(self.get(name).values()[0])

    update_preferences_from_traits = register_preferences

    def update_traits_from_preferences(self, **parameters):
        """
        """
        for name, trait in self.traits(preference = True).iteritems():

            if not parameters.has_key(name):
                continue

            value = parameters[name]
            handler = trait.handler

            # If the trait type is 'Str' then we just take the raw value.
            if isinstance(handler, Str) or trait.is_str:
                pass

            # If the trait type is 'Unicode' then we convert the raw value.
            elif isinstance(handler, Unicode):
                value = unicode(value)

            # Otherwise, we eval it!
            else:
                try:
                    value = eval(value)

                # If the eval fails then there is probably a syntax error, but
                # we will let the handler validation throw the exception.
                except:
                    pass

            if handler.validate is not None:
                # Any traits have a validator of None.
                validated = handler.validate(self, name, value)
            else:
                validated = value

            self.trait_set(**{name : validated})

    def make_parallel(self):
        pass

    def make_wait(self):
        pass

class InstrumentTask(SimpleTask):
    """Simple task involving the use of an instrument.
    """
    instr = Instance(Instrument)
    instrs = Dict(Str)
    instrs_name = List(Str)

class ComplexTask(AbstractTask):
    """Task composed of several subtasks.
    """
    children_task = List(Instance(AbstractTask))
    has_root = Bool(False)

    def __init__(self, *args, **kwargs):
        super(ComplexTask, self).__init__(*args, **kwargs)
        self._define_task_view()
        self.on_trait_change(self._update_paths,
                             name = 'task_name, task_path, task_depth')

    def process(self):
        """
        """
        for child in self.children_task:
                child.process()

    def create_child(self, ui):
        """Method to handle the adding of a child through the list editor
        """
        child = self.root_task.request_child(parent = self, ui = ui)
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
                                             self.task_name + '_' + entry, None)

        self.task_database.create_node(self.task_path, self.task_name)

        if self.children_task:
            for child in self.children_task:
                child.register_in_database()

    def unregister_from_database(self):
        """
        """
        if self.task_database_entries:
            for entry in self.task_database_entries:
                self.task_database.delete_value(self.task_path,
                                                self.task_name + '_' + entry)

        if self.children_task:
            for child in self.children_task:
                child.unregister_from_database()

        self.task_database.delete_node(self.task_path, self.task_name)

    def register_preferences(self):
        """
        """
        for name in self.traits(preference = True):
                self.task_preferences[name] = str(self.get(name).values()[0])

        for i, child in enumerate(self.children_task):
            self.task_preferences['child_{}'.format(i)] = {}
            child.task_preferences = self.task_preferences['child_{}'.format(i)]
            child.register_preferences()

    def update_preferences_from_traits(self):
        """
        """
        for name in self.traits(preference = True):
                self.task_preferences[name] = str(self.get(name).values()[0])

        for child in self.children_task:
            child.update_preferences_from_traits()

    def update_traits_from_preferences(self, **parameters):
        """

        NB : This method is fairly powerful and can handle a lot of cases so
        don't override it without checking that it works.
        """
        for name, trait in self.traits(preference = True).iteritems():

            if not parameters.has_key(name):
                continue

            value = parameters[name]
            handler = trait.handler

            #If we get a list we must determine if it is a list of child or of
            #str
            if isinstance(value, list):
                if not isinstance(value[0], basestring):
                    #We have a list of children already initialised.
                    #NB : THIS CAN BE ANYTHING INCLUDING THE TASK FOR A LOOP TASK
                    #First we check if we should pass a list or a single element
                    if isinstance(handler, List):
                        validated = value
                    else:
                        validated = value[0]
                else:
                    #We assume that we don't save anything fancier than list
                    #of string
                    if handler.validate is not None:
                        # Any traits have a validator of None.
                        validated = handler.validate(self, name, value)
                    else:
                        validated = value

            #We have a standard value store as a string, we use the standard
            #procedure
            else:
                # If the trait type is 'Str' then we just take the raw value.
                if isinstance(handler, Str) or trait.is_str:
                    pass

                # If the trait type is 'Unicode' then we convert the raw value.
                elif isinstance(handler, Unicode):
                    value = unicode(value)

                # Otherwise, we eval it!
                else:
                    try:
                        value = eval(value)
                    # If the eval fails then there is probably a syntax error, but
                    # we will let the handler validation throw the exception.
                    except:
                        pass

                if handler.validate is not None:
                    # Any traits have a validator of None.
                    validated = handler.validate(self, name, value)
                else:
                    validated = value

            self.trait_set(**{name : validated})

    @on_trait_change('children_task[]')
    def on_children_modified(self, obj, name, old, new):
        """Handle children being added or removed from the task, no matter the
        source"""
        if self.has_root:
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


    #@on_trait_change('task_name, task_path, task_depth')
    def _update_paths(self, obj, name, old, new):
        """Method taking care that the path of children, the database and the
        task name remains coherent
        """
        if self.has_root:
            if name == 'task_name':
                self.task_database.rename_node(self.task_path, new, old)
                if self.children_task:
                    for child in self.children_task:
                        child.task_path = self.task_path + new
            elif name == 'task_path':
                if self.children_task:
                    for child in self.children_task:
                        child.task_path = new + self.task_name
            elif name == 'task_depth':
                if self.children_task:
                    for child in self.children_task:
                        child.task_depth = new + 1

    def _child_added(self, child):
        """Method updating the database, depth and preference tree when a child
        is added
        """
        child.task_depth = self.task_depth + 1
        child.task_database = self.task_database
        self.task_preferences[child.task_name] = {}
        child.task_preferences = self.task_preferences[child.task_name]
        child.task_path = self.task_path + '/' + self.task_name

        #Give him its root so that it can proceed to any child
        #registration it needs to.
        child.root_task = self.root_task

        child.register_preferences()
        child.register_in_database()

    def _child_removed(self, child):
        """Method updating the database and preference tree when a child is
        removed
        """
        del self.task_preferences[child.task_name]
        child.unregister_from_database()

    @on_trait_change('root_task')
    def _when_root(self):
        """Method making sure that all children get all the info they need to
        behave correctly when the task get its root parent (ie the task is now
        in a 'correct' environnement).
        """
        self.has_root = True
        if self.children_task:
            for child in self.children_task:
                child.task_depth = self.task_depth + 1
                child.task_database = self.task_database
                self.task_preferences[child.task_name] = {}
                child.task_preferences = self.task_preferences[child.task_name]
                child.task_path = self.task_path + '/' + self.task_name

                #Give him its root so that it can proceed to any child
                #registration it needs to.
                child.root_task = self.root_task

    def _define_task_view(self):
        """
        """
        task_view = View(
                    VGroup(
                        UItem('task_name', style = 'readonly'),
                        HGroup(
                            UItem('children_task@',
                                  editor = ListInstanceEditor(
                                      style = 'custom',
                                      editor = InstanceEditor(view =
                                                              'task_view'),
                                      item_factory = self.create_child)),
                            show_border = True,
                            ),
                        ),
                        title = 'Edit task',
                    )

        self.trait_view('task_view', task_view)


class LoopTask(ComplexTask):
    """Complex task which, at each iteration, performs a task with a different
    value and all then call all its child tasks.
    """
    task = Instance(SimpleTask)
    task_start = Float(0.0, preference = True)
    task_stop = Float(1.0, preference = True)
    task_step = Float(0.1, preference = True)

    def process(self):
        """
        """
        num = int((self.task_stop - self.task_start)/self.task_step) + 1
        for value in linspace(self.task_start, self.task_stop, num):
            self.task.process(value)
            for child in self.children_task:
                child.process()

    def register_in_database(self):
        """
        """
        if self.task_database_entries:
            for entry in self.task_database_entries:
                self.task_database.set_value(self.task_path,
                                             self.task_name + '_' + entry, None)

        self.task_database.create_node(self.task_path, self.task_name)

        self.task.register_in_database()
        if self.children_task:
            for child in self.children_task:
                child.register_in_database()

    def unregister_from_database(self):
        """
        """
        if self.task_database_entries:
            for entry in self.task_database_entries:
                self.task_database.delete_value(self.task_path,
                                                self.task_name + '_' + entry)

        self.task.unregister_from_database()
        if self.children_task:
            for child in self.children_task:
                child.unregister_from_database()

        self.task_database.delete_node(self.task_path, self.task_name)

    def register_preferences(self):
        """
        """
        for name in self.traits(preference = True):
                self.task_preferences[name] = str(self.get(name).values()[0])

        self.task_preferences['task'] = {}
        self.task.task_preferences = self.task_preferences['task']
        self.task.register_preferences()
        for i, child in enumerate(self.children_task):
            self.task_preferences['child_{}'.format(i)] = {}
            child.task_preferences = self.task_preferences['child_{}'.format(i)]
            child.register_preferences()

    def update_preferences_from_traits(self):
        """
        """
        for name in self.traits(preference = True):
                self.task_preferences[name] = str(self.get(name).values()[0])

        self.task.update_preferences_from_traits()
        for child in self.children_task:
            child.update_preferences_from_traits()

    def _update_paths(self, obj, name, old, new):
        """Method taking care that the path of children, the database and the
        task name remains coherent. Here we must also care about the task.
        """
        if self.has_root:
            if name == 'task_name':
                self.task_database.rename_node(self.task_path, new, old)
                self.task.task_path = self.task_path + new
                if self.children_task:
                    for child in self.children_task:
                        child.task_path = self.task_path + new
            if name == 'task_path':
                self.task.task_path = new + self.task_name
                if self.children_task:
                    for child in self.children_task:
                        child.task_path = new + self.task_name
            if name == 'task_depth':
                self.task.task_depth = new + 1
                if self.children_task:
                    for child in self.children_task:
                        child.task_depth = new + 1

    @on_trait_change('root_task')
    def _when_root(self, new):
        """Method making sure that all children get all the info they need to
        behave correctly when the task get its root parent (ie the task is now
        in a 'correct' environnement). Here we must also take the task into
        account.
        """
        if new != None:
            self.has_root = True
            self.task.task_depth = self.task_depth + 1
            self.task.task_database = self.task_database
            self.task_preferences[self.task.task_name] = {}
            self.task.task_preferences =\
                                    self.task_preferences[self.task.task_name]
            self.task.task_path = self.task_path + '/' + self.task_name

            #Give him its root so that it can proceed to any child
            #registration it needs to.
            self.task.root_task = self.root_task
            for child in self.children_task:
                child.task_depth = self.task_depth + 1
                child.task_database = self.task_database
                self.task_preferences[child.task_name] = {}
                child.task_preferences = self.task_preferences[child.task_name]
                child.task_path = self.task_path + '/' + self.task_name

                #Give him its root so that it can proceed to any child
                #registration it needs to.
                child.root_task = self.root_task

    def _define_task_view(self):
        task_view = View(
                    UItem('task_name', style = 'readonly'),
                    VGroup(
                        VGroup(
                            Group(
                                Label('Start'), Label('Stop'), Label('Step'),
                                UItem('task_start'),UItem('task_stop'),
                                UItem('task_step'),
                                columns = 3,
                                ),
                            UItem('task', style = 'custom',
                                  editor = InstanceEditor(view = 'loop_view')),
                            show_border = True,
                            ),
                        UItem('children_task',
                          editor = ListInstanceEditor(
                              style = 'custom',
                              editor = InstanceEditor(view = 'task_view'),
                              item_factory = self.create_child)),
                        show_border = True,
                        ),
                    title = 'Edit task',
                    )
        self.trait_view('task_view', task_view)


class RootTask(ComplexTask):
    """Special task which is always the root of a measurement and is the only
    task directly referencing the measurement editor.
    """
    task_builder = Type()
    root_task = trait_self
    task_database = TaskDatabase()
    task_name = 'Root'
    task_preferences = ConfigObj()
    task_depth = 0
    task_path = 'root'
    task_database_entries = ['thread']

    def request_child(self, parent, ui):
        #the parent attribute is for now useless as all parent related traits
        #are set at adding time
        builder = self.task_builder()
        child = builder.build(parent = parent,ui = ui)
        return child

    def _child_added(self, child):
        """Method updating the database, depth and preference tree when a child
        is added
        """
        #Give the child all the info it needs to register
        child.task_depth = self.task_depth + 1
        child.task_database = self.task_database
        self.task_preferences[child.task_name] = {}
        child.task_preferences = self.task_preferences[child.task_name]
        child.task_path = self.task_path

        #Give him its root so that it can proceed to any child
        #registration it needs to.
        child.root_task = self.root_task

        #Ask the child to register
        child.register_in_database()
        child.register_preferences()

    def _child_removed(self, child):
        """Method updating the database and preference tree when a child is
        removed
        """
        del self.task_preferences[child.task_name]
        child.unregister_from_database()

    def _task_class_default(self):
        return ComplexTask.__name__

AbstractTask.add_class_trait('root_task', Instance(RootTask))