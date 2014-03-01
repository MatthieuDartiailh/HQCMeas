# -*- coding: utf-8 -*-
"""
"""

from atom.api\
    import (Atom, Str, Int, Instance, Bool, Value, observe, Unicode, List,
            ForwardTyped, Typed, ContainerList, set_default, Callable, Dict)

from configobj import Section, ConfigObj
from threading import Thread
from itertools import chain
import os

from ..atom_util import member_from_str, tagged_members
from .tools.task_database import TaskDatabase
from .tools.task_decorator import make_stoppable

class BaseTask(Atom):
    """Abstract  class defining common members of all Task

    This class basically defines the minimal skeleton of a Task in term of
    members and methods.
    """
    task_class = Str().tag(pref = True)
    task_name = Str().tag(pref = True)
    task_label = Str()
    task_depth = Int()
    task_preferences = Instance(Section)
    task_database = Typed(TaskDatabase)
    task_database_entries = Dict(Str(), Value())
    task_path = Str()
    root_task = ForwardTyped(lambda : RootTask)
    process_ = Callable()

    def process(self):
        """The main method of any task as it is this one which is called when
        the measurement is performed. This method should always be decorated
        with make_stoppable.
        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractTask. This method is called when the program requires the task\
        to be performed'
        raise NotImplementedError(err_str)

    def check(self, *args, **kwargs):
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

    def update_preferences_from_members(self):
        """Method used to update the entries in the preference object before
        saving
        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractTask. This method is called when the program requires the task\
        to update the entries in the preference object before saving'
        raise NotImplementedError(err_str)

    def update_members_from_preferences(self, **parameters):
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

    def _default_task_class(self):
        """
        """
        return self.__class__.__name__

    def _default_process_(self):
        """
        """
        return self.process.__func__

    def _observe_task_name(self, change):
        """
        """
        new = change['value']
        self.task_label = new + ' (' + self.task_class + ')'

    @observe('task_database_entries')
    def _update_database(self, change):
        """
        """
        if change['type'] == 'update':
            added = set(change['value']) - set(change['oldvalue'])
            removed = set(change['oldvalue']) - set(change['value'])
            if self.task_database:
                for entry in removed:
                    self.remove_from_database(self.task_name + '_' + entry)
                for entry in added:
                    self.write_in_database(entry,
                                           self.task_database_entries[entry])

    def _list_database_entries(self):
        """
        """
        return self.task_database.list_accessible_entries(self.task_path)

class SimpleTask(BaseTask):
    """Task with no child task, written in pure Python.
    """
    #Class attribute specifying if instances of that class can be used in loop
    # Not a Trait because otherwise would not be a class attribute
    loopable = False
    _parallel = Dict(Str(), default = {'activated' : False, 'pool' : ''})
    _wait = Dict(Str(), List())

    def write_in_database(self, name, value):
        """This method build a task specific database entry from the task_name
        and the name argument and set the database entry to the specified value.
        """
        value_name = self.task_name + '_' + name
        return self.task_database.set_value(self.task_path, value_name, value)

    def get_from_database(self, full_name):
        """This method return the value under the database entry specified by
        the full name (ie task_name + '_' + entry, where task_name is the name
        of the task that wrote the value in the database).
        """
        return self.task_database.get_value(self.task_path, full_name)

    def remove_from_database(self, full_name):
        """This method deletes the database entry specified by
        the full name (ie task_name + '_' + entry, where task_name is the name
        of the task that wrote the value in the database).
        """
        return self.task_database.delete_value(self.task_path, full_name)

    def register_in_database(self):
        """
        """
        if self.task_database_entries:
            for entry in self.task_database_entries:
                self.task_database.set_value(self.task_path,
                                             self.task_name + '_' + entry,
                                             self.task_database_entries[entry])

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
        self.task_preferences.clear()
        for name in tagged_members(self, 'pref'):
            self.task_preferences[name] = str(getattr(self, name))

    update_preferences_from_members = register_preferences

    def update_members_from_preferences(self, **parameters):
        """
        """
        for name, member in tagged_members(self, 'pref').iteritems():

            if not parameters.has_key(name):
                continue

            value = parameters[name]
            converted = member_from_str(member, value)
            setattr(self, name, converted)

    def make_parallel(self, pool, switch = ''):
        """This method should be called in __init__ when there is no need to
        wait for the process method to return to start the next task,ie the
        process method decorated don't use any data succeptible to be corrupted
        by the next task.
        """
        par = self._parallel
        par['pool'] = pool
        par['activated'] = getattr(self, switch, True)
        if switch:
            self.observe('switch', self._redefine_process_)
        self._redefine_process_()

    def make_wait(self, wait = [], no_wait = []):
        """This method should be be called in __init__ when the process method
        need to access data in the database or need to be sure that physical
        quantities reached their expected values.
        """
        _wait = self._wait
        _wait['wait'] = wait
        _wait['no_wait'] = no_wait
        self._redefine_process_()

    def _redefine_process_(self, change = None):
        """
        """
        if change:
            self._parallel['activated'] = change['value']
        process = self.process.__func__
        parallel = self._parallel
        if parallel['activated'] and parallel['pool']:
            process = self._make_parallel_process_(process, parallel['pool'])

        wait = self._wait
        if 'wait' in wait and 'no_wait' in wait:
            process = self._make_wait_process_(process,
                                               wait['wait'],
                                               wait['no_wait'])

        self.process_ = make_stoppable(process)

    @staticmethod
    def _make_parallel_process_(process, pool):
        """
        """
        def wrapper(*args, **kwargs):

            obj = args[0]
            thread = Thread(group = None,
                            target = process,
                            args = args,
                            kwargs = kwargs)
            all_threads = obj.task_database.get_value('root', 'threads')
            threads = all_threads.get(pool, None)
            if threads:
                threads.append(thread)
            else:
                all_threads[pool] = [thread]

            return thread.start()

        wrapper.__name__ = process.__name__
        wrapper.__doc__ = process.__doc__
        return wrapper

    @staticmethod
    def _make_wait_process_(process, wait, no_wait):
        """
        """
        if wait:
            def wrapper(*args, **kwargs):

                obj = args[0]
                all_threads = obj.task_database.get_value('root', 'threads')

                threads = chain([all_threads.get(w, []) for w in wait])
                for thread in threads:
                    thread.join()
                all_threads.update({w : [] for w in wait if w in all_threads})

                obj.task_database.set_value('root', 'threads', all_threads)
                return process(*args, **kwargs)
        elif no_wait:
            def wrapper(*args, **kwargs):

                obj = args[0]
                all_threads = obj.task_database.get_value('root', 'threads')

                pools = [k for k in all_threads if k not in no_wait]
                threads = chain([all_threads[p] for p in pools])
                for thread in threads:
                    thread.join()
                all_threads.update({p : [] for p in pools})

                obj.task_database.set_value('root', 'threads', all_threads)
                return process(*args, **kwargs)
        else:
            def wrapper(*args, **kwargs):

                obj = args[0]
                all_threads = obj.task_database.get_value('root', 'threads')

                threads = chain(all_threads.values())
                for thread in threads:
                    thread.join()
                all_threads.update({w : [] for w in all_threads})

                obj.task_database.set_value('root', 'threads', all_threads)
                return process(*args, **kwargs)

        wrapper.__name__ = process.__name__
        wrapper.__doc__ = process.__doc__

        return wrapper

class ComplexTask(BaseTask):
    """Task composed of several subtasks.
    """
    children_task = ContainerList(Instance(BaseTask)).tag(child = True)
    has_root = Bool(False)

    def __init__(self, *args, **kwargs):
        super(ComplexTask, self).__init__(*args, **kwargs)
        self.observe('task_name', self._update_paths)
        self.observe('task_path', self._update_paths)
        self.observe('task_depth', self._update_paths)

    @make_stoppable
    def process(self):
        """
        """
        for child in self.children_task:
            child.process_(child)

    def check(self, *args, **kwargs):
        """Implementation of the test method of AbstractTask
        """
        test = True
        traceback = {}
        for name in tagged_members(self, 'child'):
            child = getattr(self, name)
            if child:
                if isinstance(child, list):
                    for aux in child:
                        check = aux.check(*args, **kwargs)
                        test = test and check[0]
                        traceback.update(check[1])
                else:
                    check = child.check(*args, **kwargs)
                    test = test and check[0]
                    traceback.update(check[1])

        return test, traceback

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

    def remove_from_database(self, full_name):
        """This method deletes the database entry specified by
        the full name (ie task_name + '_' + entry, where task_name is the name
        of the task that wrote the value in the database).
        """
        return self.task_database.delete_value(self.task_path, full_name)

    def register_in_database(self):
        """
        """
        if self.task_database_entries:
            for entry in self.task_database_entries:
                self.task_database.set_value(self.task_path,
                                             self.task_name + '_' + entry,
                                             self.task_database_entries[entry])

        self.task_database.create_node(self.task_path, self.task_name)

        #ComplexTask defines children_task so we always get something
        for name in tagged_members(self, 'child'):
            child = getattr(self, name)
            if child:
                if isinstance(child, list):
                    for aux in child:
                        aux.register_in_database()
                else:
                    child.register_in_database()

    def unregister_from_database(self):
        """
        """
        if self.task_database_entries:
            for entry in self.task_database_entries:
                self.task_database.delete_value(self.task_path,
                                                self.task_name + '_' + entry)

        for name in tagged_members(self, 'child'):
            child = getattr(self, name)
            if child:
                if isinstance(child, list):
                    for aux in child:
                        aux.unregister_from_database()
                else:
                    child.unregister_from_database()

        self.task_database.delete_node(self.task_path, self.task_name)

    def register_preferences(self):
        """
        """
        self.task_preferences.clear()
        members = self.members()
        for name in members:
            meta = members[name].metadata
            if meta and 'pref' in meta:
                self.task_preferences[name] = str(getattr(self, name))

            elif meta and 'child' in meta:
                child = getattr(self, name)
                if child:
                    if isinstance(child, list):
                        for i, aux in enumerate(child):
                            child_id = name + '_{}'.format(i)
                            self.task_preferences[child_id] = {}
                            aux.task_preferences = \
                                            self.task_preferences[child_id]
                            aux.register_preferences()
                    else:
                        self.task_preferences[name] = {}
                        child.task_preferences = self.task_preferences[name]
                        child.register_preferences()

    def update_preferences_from_members(self):
        """
        """
        for name in tagged_members(self, 'pref'):
            self.task_preferences[name] = str(getattr(self, name))

        for name in tagged_members(self, 'child'):
            child =  getattr(self, name)
            if child:
                if isinstance(child, list):
                    for aux in child:
                        aux.update_preferences_from_members()
                else:
                    child.update_preferences_from_members()

    def update_members_from_preferences(self, **parameters):
        """

        NB : This method is fairly powerful and can handle a lot of cases so
        don't override it without checking that it works.
        """
        #First we set the preference members
        for name, member in self.members().iteritems():
            meta = member.metadata
            if meta and 'pref' in meta :
                if not parameters.has_key(name):
                    continue

                # member_from_str handle containers
                value = parameters[name]
                validated = member_from_str(member, value)

                setattr(self, name, validated)

            elif meta and 'child' in meta:
                if not parameters.has_key(name):
                    continue

                value = parameters[name]

                if isinstance(member, ContainerList):
                    validated = value
                else:
                    validated = value[0]

                setattr(self, name, validated)

    def walk(self, members = [], callables = {}):
        """
        """
        answer = [self._answer(self, members, callables)]
        for task in self.children_task:
            if isinstance(task, SimpleTask):
                answer.append(self._answer(task, members, callables))
            else:
                answer.append(task.walk(members, callables))

        return answer

    @staticmethod
    def _answer(obj, members, callables):
        """
        """
        answers = {m : getattr(obj, m, None) for m in members}
        answers.update({k : c(obj) for k,c in callables.iteritems()})
        return answers

    @observe('children_task')
    def on_children_modified(self, change):
        """Handle children being added or removed from the task, no matter the
        source"""
        if self.has_root:
            if change['type'] == 'update':
                added = set(change['value']) - set(change['oldvalue'])
                removed = set(change['oldvalue']) - set(change['value'])
                for child in removed:
                    self._child_removed(child)
                for child in added:
                    self._child_added(child)
            elif change['type'] == 'container':
                op = change['operation']
                if op in ('__iadd__', 'append', 'extend', 'insert'):
                    if 'item' in change:
                        self._child_added(change['item'])
                    if 'items' in change:
                        for child in change['items']:
                            self._child_added(child)

                elif op in ('__delitem__', 'remove', 'pop'):
                    if 'item' in change:
                        self._child_removed(change['item'])
                    if 'items' in change:
                        for child in change['items']:
                            self._child_removed(child)

                elif op in ('__setitem__'):
                    old = change['olditem']
                    if isinstance(old, list):
                        for child in old:
                            self._child_removed(child)
                    else:
                        self._child_removed(old)

                    new = change['newitem']
                    if isinstance(new, list):
                        for child in new:
                            self._child_added(child)
                    else:
                        self._child_added(new)

    #@observe('task_name, task_path, task_depth')
    def _update_paths(self, change):
        """Method taking care that the path of children, the database and the
        task name remains coherent
        """
        if change['type'] == 'update':
            name = change['name']
            new = change['value']
            old = change.get('oldvalue', None)
            if self.has_root:
                if name == 'task_name':
                    self.task_database.rename_node(self.task_path, new, old)
                    for name in tagged_members(self, 'child'):
                        child = getattr(self, name)
                        if child:
                            if isinstance(child, list):
                                for aux in child:
                                    aux.task_path = self.task_path + '/' + new
                            else:
                                child.task_path = self.task_path + '/' + new
                elif name == 'task_path':
                    for name in tagged_members(self, 'child'):
                        child = getattr(self, name)
                        if child:
                            if isinstance(child, list):
                                for aux in child:
                                    aux.task_path = new + '/' + self.task_name
                            else:
                                child.task_path = new + '/' + self.task_name
                elif name == 'task_depth':
                    for name in tagged_members(self, 'child'):
                        child = getattr(self, name)
                        if child:
                            if isinstance(child, list):
                                for aux in child:
                                    aux.task_depth = new + 1
                            else:
                                child.task_depth = new + 1


    def _child_added(self, child):
        """Method updating the database, depth and preference tree when a child
        is added
        """
        child.task_depth = self.task_depth + 1
        child.task_database = self.task_database
        child.task_path = self.task_path + '/' + self.task_name

        #Give him its root so that it can proceed to any child
        #registration it needs to.
        child.root_task = self.root_task

        #Ask the child to register in database
        child.register_in_database()
        #Register anew preferences to keep the right ordering for the childs
        self.register_preferences()

    def _child_removed(self, child):
        """Method updating the database and preference tree when a child is
        removed.
        """
        self.register_preferences()
        child.unregister_from_database()

    @observe('root_task')
    def _when_root(self, change):
        """Method making sure that all children get all the info they need to
        behave correctly when the task get its root parent (ie the task is now
        in a 'correct' environnement).
        """
        if change['value'] == None:
            return

        self.has_root = True
        for name in tagged_members(self, 'child'):
            child = getattr(self, name)
            if child:
                if isinstance(child, list):
                    for aux in child:
                        aux.task_depth = self.task_depth + 1
                        aux.task_database = self.task_database
                        aux.task_path = self.task_path + '/' + self.task_name

                        #Give him its root so that it can proceed to any child
                        #registration it needs to.
                        aux.root_task = self.root_task
                else:
                    child.task_depth = self.task_depth + 1
                    child.task_database = self.task_database
                    child.task_path = self.task_path + '/' + self.task_name

                    #Give him its root so that it can proceed to any child
                    #registration it needs to.
                    child.root_task = self.root_task

from multiprocessing.synchronize import Event


class RootTask(ComplexTask):
    """Special task which is always the root of a measurement and is the only
    task directly referencing the measurement editor.
    """
    default_path = Unicode('').tag(pref = True)
    has_root = set_default(True)
    task_name = set_default('Root')
    task_label = set_default('Root')
    task_preferences = ConfigObj(indent_type = '    ')
    task_depth = set_default(0)
    task_path = set_default('root')
    task_database_entries = set_default({'threads' : [],
                                         'instrs' : {},
                                         'default_path' : ''})
    should_stop = Instance(Event)

    def __init__(self, *args, **kwargs):
        super(RootTask, self).__init__(*args, **kwargs)
        self.task_database = TaskDatabase()
        self.task_database.set_value('root', 'threads', {})
        self.task_database.set_value('root', 'instrs', {})
        self.root_task = self

    def check(self, *args, **kwargs):
        traceback = {}
        test = True
        if not os.path.isdir(self.default_path):
            test = False
            traceback[self.task_path + '/' + self.task_name] =\
                'The provided default path is not a valid directory'
        self.task_database.set_value('root', 'default_path', self.default_path)
        check = super(RootTask, self).check(*args, **kwargs)
        test = test and check[0]
        traceback.update(check[1])
        return test, traceback

    @make_stoppable
    def process(self):
        """
        """
        for child in self.children_task:
            child.process_(child)
        pools = self.task_database.get_value('root','threads')
        for pool in pools.items():
            for thread in pool:
                thread.join()
        instrs = self.task_database.get_value('root','instrs')
        for instr_profile in instrs:
            instrs[instr_profile].close_connection()

    def _child_added(self, child):
        """Method updating the database, depth and preference tree when a child
        is added
        """
        #Give the child all the info it needs to register
        child.task_depth = self.task_depth + 1
        child.task_database = self.task_database
        child.task_path = self.task_path

        #Give him its root so that it can proceed to any child
        #registration it needs to.
        child.root_task = self.root_task

        #Ask the child to register in database
        child.register_in_database()
        #Register anew preferences to keep the right ordering for the childs
        self.register_preferences()

    def _task_class_default(self):
        return ComplexTask.__name__

    @observe('default_path')
    def _update_default_path_in_database(self, change):
        """
        """
        new = change['value']
        if new:
            self.default_path = os.path.normpath(new)
            self.task_database.set_value('root', 'default_path',
                                         self.default_path)
