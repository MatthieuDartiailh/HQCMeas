# -*- coding: utf-8 -*-
# =============================================================================
# module : base_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api\
    import (Atom, Str, Int, Instance, Bool, Value, observe, Unicode, List,
            ForwardTyped, Typed, ContainerList, set_default, Callable, Dict,
            Tuple, Coerced)

from configobj import Section, ConfigObj
from inspect import cleandoc
from copy import deepcopy
import os
import datetime
import logging

from ..utils.atom_util import member_from_str, tagged_members
from .tools.task_database import TaskDatabase
from .tools.task_decorator import (make_parallel, make_wait, make_stoppable,
                                   smooth_crash)
from .tools.string_evaluation import safe_eval
from .tools.shared_resources import SharedDict, SharedCounter


PREFIX = '_a'


class BaseTask(Atom):
    """Base  class defining common members of all Tasks.

    This class basically defines the minimal skeleton of a Task in term of
    members and methods.

    """
    # --- Public API ----------------------------------------------------------
    #: Name of the class, used for persistence.
    task_class = Str().tag(pref=True)

    #: Name of the task this should be unique in hierarchy.
    task_name = Str().tag(pref=True)

    #: Label of the task to display in the tree editor.
    # XXXX this requires some reformating.
    task_label = Str()

    #: Depth of the task in the hierarchy. this should not be manipulated
    #: directly by user code.
    task_depth = Int()

    #: Reference to the Section in which the task stores its preferences.
    task_preferences = Instance(Section)

    #: Reference to the database used by the task to exchange information.
    task_database = Typed(TaskDatabase)

    #: Entries the task declares in the database and the associated default
    #: values.
    task_database_entries = Dict(Str(), Value())

    #: Path of the task in the hierarchy. This refers to the parent task and
    #: is used when writing in the database.
    task_path = Str()

    #: Reference to the root task in the hierarchy.
    root_task = ForwardTyped(lambda: RootTask)

    #: Refrence to the parent task.
    parent_task = ForwardTyped(lambda: BaseTask)

    #: Unbound method called when the task is asked to do its job. This is
    #: basically the perform method but wrapped with useful stuff such as
    #: interruption check or parallel, wait features.
    perform_ = Callable()

    #: Flag indicating if this task can be stopped.
    stoppable = Bool(True).tag(pref=True)

    #: Dictionary indicating whether the task is executed in parallel
    #: ('activated' key) and which is pool it belongs to ('pool' key).
    parallel = Dict(Str()).tag(pref=True)

    #: Dictionary indicating whether the task should wait on any pool before
    #: performing its job. Three valid keys can be used :
    #: - 'activated' : a bool indicating whether or not to wait.
    #: - 'wait' : the list should then specify which pool should be waited.
    #: - 'no_wait' : the list should specify which pool not to wait on.
    wait = Dict(Str()).tag(pref=True)

    def __init__(self, **kwargs):
        """ Overridden init to make sure perform is wrapped correctly.

        """
        super(BaseTask, self).__init__(**kwargs)
        self._redefine_perform_()

    def perform(self):
        """ The main method of any task as it is this one which is called when
        the measurement is performed. This method should always be decorated
        with make_stoppable, and return True if things went well.

        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractTask. This method is called when the program requires the task\
        to be performed'
        raise NotImplementedError(cleandoc(err_str))

    def check(self, *args, **kwargs):
        """ Method used to check that everything is alright before starting a
        measurement.

        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractTask. This method is called when the program requires the task\
        to check that all parameters are ok'
        raise NotImplementedError(cleandoc(err_str))

    def answer(self, members, callables):
        """ Method used by to retrieve information about a task.

        Parameters
        ----------
        members : list(str)
            List of members names whose values should be returned.

        callables : dict(str, callable)
            Dict of name callable to invoke on the task or interface to get
            some infos.

        Returns
        -------
        infos : dict
            Dict holding all the answers for the specified members and
            callables.

        """
        answers = {m: getattr(self, m, None) for m in members}
        answers.update({k: c(self) for k, c in callables.iteritems()})
        return answers

    def register_in_database(self):
        """ Method used to create entries in the database.

        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractTask. This method is called when the program requires the task\
        to create its entry in the database'
        raise NotImplementedError(cleandoc(err_str))

    def unregister_from_database(self):
        """ Method used to delete entries from the database.

        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractTask. This method is called when the program requires the task\
        to delete its entry from the database'
        raise NotImplementedError(cleandoc(err_str))

    def register_preferences(self):
        """ Method used to create entries in the preferences object.

        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractTask. This method is called when the program requires the task\
        to create its entries in the preferences object'
        raise NotImplementedError(cleandoc(err_str))

    def update_preferences_from_members(self):
        """ Method used to update the entries in the preference object before
        saving.

        """
        err_str = 'This method should be implemented by subclasses of\
        AbstractTask. This method is called when the program requires the task\
        to update the entries in the preference object before saving'
        raise NotImplementedError(cleandoc(err_str))

    @classmethod
    def build_from_config(cls, config, dependencies):
        """ Create a new instance using the provided infos for initialisation.

        Parameters
        ----------
        config : dict(str)
            Dictionary holding the new values to give to the members in string
            format, or dictionnary like for instance with prefs.

        dependencies : dict
            Dictionary holding the necessary classes needed when rebuilding.
            This is assembled by the TaskManager.

        """
        err_str = '''This method should be implemented by subclasses of
        AbstractTask. This method is called when the program requires the task
        to reconstruct itself using the infos stored in a dictionary.'''
        raise NotImplementedError(cleandoc(err_str))

    def accessible_database_entries(self):
        """ Convenience to get the accesible entries in the database.

        """
        return self.task_database.list_accessible_entries(self.task_path)

    def format_string(self, string):
        """ Replace values in {} by their corresponding database value.

        Parameters
        ----------
        string : str
            The string to format using the current values of the database.

        Returns
        -------
        formatted : str
            Formatted version of the input.

        """
        # If a cache evaluation of the string already exists use it.
        if string in self._format_cache:
            preformatted, ids = self._format_cache[string]
            vals = self.task_database.get_values_by_index(ids, PREFIX)
            return preformatted.format(**vals)

        # Otherwise if we are in running mode build a cache formatting.
        elif self.task_database.running:
            database = self.task_database
            aux_strings = string.split('{')
            if len(aux_strings) > 1:
                elements = [el
                            for aux in aux_strings
                            for el in aux.split('}')]
                database_indexes = database.get_entries_indexes(self.task_path,
                                                                elements[1::2])
                str_to_format = ''
                length = len(elements)
                for i in range(0, length, 2):
                    if i + 1 < length:
                        repl = PREFIX + str(database_indexes[elements[i + 1]])
                        str_to_format += elements[i] + '{' + repl + '}'
                    else:
                        str_to_format += elements[i]

                indexes = database_indexes.values()
                self._format_cache[string] = (str_to_format, indexes)
                vals = self.task_database.get_values_by_index(indexes, PREFIX)
                return str_to_format.format(**vals)
            else:
                self._format_cache[string] = (string, [])
                return string

        # In edition mode simply perfom the formatting as execution time is not
        # critical.
        else:
            database = self.task_database
            aux_strings = string.split('{')
            if len(aux_strings) > 1:
                elements = [el
                            for aux in aux_strings
                            for el in aux.split('}')]
                replacement_values = [database.get_value(self.task_path, key)
                                      for key in elements[1::2]]
                str_to_format = ''
                for key in elements[::2]:
                    str_to_format += key + '{}'

                str_to_format = str_to_format[:-2]

                return str_to_format.format(*replacement_values)
            else:
                return string

    def format_and_eval_string(self, string):
        """ Replace values in {} by their corresponding database value and eval

        Parameters
        ----------
        string : str
            The string to eval using the current values of the database.

        Returns
        -------
        formatted : str
            Formatted version of the input.

        """
        # If a cache evaluation of the string already exists use it.
        if string in self._eval_cache:
            preformatted, ids = self._eval_cache[string]
            vals = self.task_database.get_values_by_index(ids, PREFIX)
            return safe_eval(preformatted, vals)

        # Otherwise if we are in running mode build a cache evaluation.
        elif self.task_database.running:
            database = self.task_database
            aux_strings = string.split('{')
            if len(aux_strings) > 1:
                elements = [el
                            for aux in aux_strings
                            for el in aux.split('}')]
                database_indexes = database.get_entries_indexes(self.task_path,
                                                                elements[1::2])
                str_to_eval = ''
                length = len(elements)
                for i in range(0, length, 2):
                    if i + 1 < length:
                        repl = PREFIX + str(database_indexes[elements[i + 1]])
                        str_to_eval += elements[i] + repl
                    else:
                        str_to_eval += elements[i]

                indexes = database_indexes.values()
                self._eval_cache[string] = (str_to_eval, indexes)
                vals = self.task_database.get_values_by_index(indexes, PREFIX)
                return safe_eval(str_to_eval, vals)
            else:
                self._eval_cache[string] = (string, [])
                return safe_eval(string)

        # In edition mode simply perfom the evaluation as execution time is not
        # critical.
        else:
            database = self.task_database
            aux_strings = string.split('{')
            if len(aux_strings) > 1:
                elements = [el
                            for aux in aux_strings
                            for el in aux.split('}')]
                replacement_token = [PREFIX + str(i)
                                     for i in xrange(len(elements[1::2]))]
                repl = {PREFIX + str(i): database.get_value(self.task_path,
                                                            key)
                        for i, key in enumerate(elements[1::2])}
                str_to_format = ''
                for key in elements[::2]:
                    str_to_format += key + '{}'

                str_to_format = str_to_format[:-2]

                expr = str_to_format.format(*replacement_token)
                return safe_eval(expr, repl)
            else:
                return safe_eval(string)

    # --- Private API ---------------------------------------------------------

    #: Dictionary storing in infos necessary to perform fast formatting.
    #: Only used in running mode.
    _format_cache = Dict()

    #: Dictionary storing in infos necessary to perform fast evaluation.
    #: Only used in running mode.
    _eval_cache = Dict()

    def _default_task_class(self):
        """ Default value for the task_class member.

        """
        return self.__class__.__name__

    def _observe_task_name(self, change):
        """ Update the label any time the task name changes.

        """
        new = change['value']
        self.task_label = new + ' (' + self.task_class + ')'

    @observe('task_database_entries')
    def _update_database(self, change):
        """ Update the database content each time the database entries change.

        """
        if change['type'] == 'update':
            added = set(change['value']) - set(change['oldvalue'])
            removed = set(change['oldvalue']) - set(change['value'])
            if self.task_database:
                for entry in removed:
                    self.remove_from_database(self.task_name + '_' + entry)
                for entry in added:
                    new_value = deepcopy(self.task_database_entries[entry])
                    self.write_in_database(entry, new_value)

    @observe('wait', 'parallel', 'stopable')
    def _parallell_wait_update(self, change):
        """

        """
        self._redefine_perform_()

    def _redefine_perform_(self):
        """ Make perform_ refects the parallel/wait settings.

        """
        perform_func = self.perform.__func__
        parallel = self.parallel
        if parallel.get('activated') and parallel.get('pool'):
            perform_func = make_parallel(perform_func, parallel['pool'])

        wait = self.wait
        if wait.get('activated'):
            perform_func = make_wait(perform_func,
                                     wait.get('wait'),
                                     wait.get('no_wait'))

        if self.stoppable:
            self.perform_ = make_stoppable(perform_func)
        else:
            self.perform_ = perform_func


class SimpleTask(BaseTask):
    """ Task with no child task, written in pure Python.

    """
    # --- Public API ----------------------------------------------------------

    #: Class attribute specifying if that task can be used in a loop
    loopable = False

    def check(self, *args, **kwargs):
        """ Empty check allowing super to call this method and not raise any
        NotImplementedError.

        """

        return True, {}

    def write_in_database(self, name, value):
        """ Write a value to the right database entry.

        This method build a task specific database entry from the task_name
        and the name argument and set the database entry to the specified
        value.

        Parameters
        ----------
        name : str
            Simple name of the entry whose value should be set, ie no task name
            required.

        value:
            Value to give to the entry.

        """
        value_name = self.task_name + '_' + name
        return self.task_database.set_value(self.task_path, value_name, value)

    def get_from_database(self, full_name):
        """ Access to a database value using full name.

        Parameters
        ----------
        full_name : str
            Full name of the database entry, ie task_name + '_' + entry,
            where task_name is the name of the task that wrote the value in
            the database.

        """
        return self.task_database.get_value(self.task_path, full_name)

    def remove_from_database(self, full_name):
        """ Delete a database entry using its full name.

        Parameters
        ----------
        full_name : str
            Full name of the database entry, ie task_name + '_' + entry,
            where task_name is the name of the task that wrote the value in
            the database.

        """
        return self.task_database.delete_value(self.task_path, full_name)

    def register_in_database(self):
        """ Register the task entries into the database.

        """
        if self.task_database_entries:
            for entry in self.task_database_entries:
                # Perform a deepcopy of the entry value as I don't want to
                # alter that default value when dealing with the database later
                # on (apply for list and dict).
                value = deepcopy(self.task_database_entries[entry])
                self.task_database.set_value(self.task_path,
                                             self.task_name + '_' + entry,
                                             value)

    def unregister_from_database(self):
        """ Remove the task entries from the database.

        """
        if self.task_database_entries:
            for entry in self.task_database_entries:
                self.task_database.delete_value(self.task_path,
                                                self.task_name + '_' + entry)

    def register_preferences(self):
        """ Register the task preferences into the preferences system.

        """
        self.task_preferences.clear()
        for name in tagged_members(self, 'pref'):
            val = getattr(self, name)
            if isinstance(val, basestring):
                self.task_preferences[name] = val
            else:
                self.task_preferences[name] = repr(val)

    update_preferences_from_members = register_preferences

    @classmethod
    def build_from_config(cls, config, dependencies):
        """ Create a new instance using the provided infos for initialisation.

        Parameters
        ----------
        config : dict(str)
            Dictionary holding the new values to give to the members in string
            format, or dictionnary like for instance with prefs.

        dependencies : dict
            Dictionary holding the necessary classes needed when rebuilding.
            This is assembled by the TaskManager.

        """
        task = cls()
        for name, member in tagged_members(task, 'pref').iteritems():

            if name not in config:
                continue

            value = config[name]
            converted = member_from_str(member, value)
            setattr(task, name, converted)

        return task


class ComplexTask(BaseTask):
    """Task composed of several subtasks.

    """
    # --- Public API ----------------------------------------------------------

    #: List of all the children of the task.
    children_task = ContainerList(Instance(BaseTask)).tag(child=True)

    #: Dict of access exception in the database. This should not be manipulated
    #: by user code.
    access_exs = ContainerList().tag(pref=True)

    #: Flag indicating whether or not the task has a root task.
    has_root = Bool(False)

    def __init__(self, *args, **kwargs):
        super(ComplexTask, self).__init__(*args, **kwargs)
        self.observe('task_name', self._update_paths)
        self.observe('task_path', self._update_paths)
        self.observe('task_depth', self._update_paths)

    def perform(self):
        """ Run sequentially all child tasks.

        """
        for child in self.children_task:
            child.perform_(child)

    def check(self, *args, **kwargs):
        """ Run test of all child tasks.

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

    def walk(self, members=[], callables={}):
        """ Explore the tasks hierarchy looking.

        Missing values will be filled with None.

        Parameters
        ----------
        members : list(str)
            Names of the members whose value should be retrieved.

        callables : dict(callable)
            Dict {name: callables} to call on every task in the hierarchy. Each
            callable should take as single argument the task.

        Returns
        -------
        answer : list
            List summarizing the result of the exploration.

        """
        answer = [self.answer(members, callables)]
        for task in self._gather_children_task():
            if isinstance(task, SimpleTask):
                answer.append(task.answer(members, callables))
            elif task:
                answer.append(task.walk(members, callables))

        return answer

    def write_in_database(self, name, value):
        """ Write a value to the right database entry.

        This method build a task specific database entry from the task_name
        and the name argument and set the database entry to the specified
        value.

        Parameters
        ----------
        name : str
            Simple name of the entry whose value should be set, ie no task name
            required.

        value:
            Value to give to the entry.

        """
        value_name = self.task_name + '_' + name
        return self.task_database.set_value(self.task_path, value_name, value)

    def get_from_database(self, full_name):
        """ Access to a database value using full name.

        Parameters
        ----------
        full_name : str
            Full name of the database entry, ie task_name + '_' + entry,
            where task_name is the name of the task that wrote the value in
            the database.

        """
        return self.task_database.get_value(self.task_path, full_name)

    def remove_from_database(self, full_name):
        """ Delete a database entry using its full name.

        Parameters
        ----------
        full_name : str
            Full name of the database entry, ie task_name + '_' + entry,
            where task_name is the name of the task that wrote the value in
            the database.

        """
        return self.task_database.delete_value(self.task_path, full_name)

    def register_in_database(self):
        """ Create a node in the database and register all entries.

        This method registers both the task entries and all the tasks tagged
        as child.

        """
        if self.task_database_entries:
            for entry in self.task_database_entries:
                # Perform a deepcopy of the entry value as I don't want to
                # alter that default value when dealing with the database later
                # on (apply for list and dict).
                value = deepcopy(self.task_database_entries[entry])
                self.task_database.set_value(self.task_path,
                                             self.task_name + '_' + entry,
                                             value)

        self.task_database.create_node(self.task_path, self.task_name)

        # ComplexTask defines children_task so we always get something
        for child in self._gather_children_task():
            child.register_in_database()

        # Add access exception in database.
        self._refresh_access_exceptions()

    def unregister_from_database(self):
        """ Unregister all entries and delete associated database node.

        This method unregisters both the task entries and all the tasks tagged
        as child.

        """
        # Remove access exception from database.
        self._refresh_access_exceptions(removed=self.access_exs)

        if self.task_database_entries:
            for entry in self.task_database_entries:
                self.task_database.delete_value(self.task_path,
                                                self.task_name + '_' + entry)

        for child in self._gather_children_task():
            child.unregister_from_database()

        self.task_database.delete_node(self.task_path, self.task_name)

    def add_access_exception(self, entry):
        """ Add an access exception for an entry.

        This make a child entry equivalent to a task entry with respact to the
        database.

        This method first look for the location of the entry to determine if it
        exists and whether or not it is itself an access exception. If it is an
        access exception add an observer to the child to be notified when this
        exception is removed.

        Parameters
        ----------
        entry : str
            Full name of the entry database for which to add an exception.
            This entry must be present in one of the task children.

        """
        database = self.task_database
        # Find the child declaring the entry to get the path and
        # determine if the entry is an access exception.
        for child in self._gather_children_task():
            entries = [child.task_name + '_' + e
                       for e in child.task_database_entries]
            if entry in entries:
                database.add_access_exception(self.task_path,
                                              entry, child.task_path)
                self.access_exs.append(entry)
                return

            elif hasattr(child, 'access_exs') and entry in child.access_exs:
                database.add_access_exception(self.task_path,
                                              entry, child.task_path)
                child.observe('access_exs', self._child_access_exs_changed)
                self.access_exs.append(entry)
                return

        raise KeyError('Entry {} is not accessible from task {}'.format(entry,
                       self.task_name))

    def remove_access_exception(self, entry):
        """ Remove the access exception for an entry.

        Parameters
        ----------
        entry_name : str
            Full name of the entry database for which to remove an exception.

        """
        # Check that the entry is known.
        if entry not in self.access_exs:
            raise KeyError('No access exception for entry {} in {}.'.format(
                           entry, self.task_name))

        database = self.task_database
        # Find the child declaring the entry to determine if the
        # entry is an access exception.
        for child in self._gather_children_task():
            entries = [child.task_name + '_' + e
                       for e in child.task_database_entries]
            if entry in entries:
                database.remove_access_exception(self.task_path,
                                                 entry)
                self.access_exs.remove(entry)
                return

            elif hasattr(child, 'access_exs') and entry in child.access_exs:
                database.remove_access_exception(self.task_path,
                                                 entry)
                child.unobserve('access_exs', self._child_access_exs_changed)
                self.access_exs.remove(entry)
                return

    def register_preferences(self):
        """ Register the task preferences into the preferences system.

        This method registers both the task preferences and all the
        preferences of the tasks tagged as child.

        """
        self.task_preferences.clear()
        members = self.members()
        for name in members:
            # Register preferences.
            meta = members[name].metadata
            if meta and 'pref' in meta:
                val = getattr(self, name)
                if isinstance(val, basestring):
                    self.task_preferences[name] = val
                else:
                    self.task_preferences[name] = repr(val)

            # Find all tagged children.
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
        """ Update the values stored in the preference system.

        This method updates both the task preferences and all the
        preferences of the tasks tagged as child.

        """
        for name in tagged_members(self, 'pref'):
            val = getattr(self, name)
            if isinstance(val, basestring):
                self.task_preferences[name] = val
            else:
                self.task_preferences[name] = repr(val)

        for child in self._gather_children_task():
            child.update_preferences_from_members()

    @classmethod
    def build_from_config(cls, config, dependencies):
        """ Create a new instance using the provided infos for initialisation.

        Parameters
        ----------
        config : dict(str)
            Dictionary holding the new values to give to the members in string
            format, or dictionnary like for instance with prefs.

        dependencies : dict
            Dictionary holding the necessary classes needed when rebuilding.
            This is assembled by the TaskManager.

        Returns
        -------
        task :
            Newly created and initiliazed task.

        Notes
        -----
        This method is fairly powerful and can handle a lot of cases so
        don't override it without checking that it works.

        """
        task = cls()
        for name, member in task.members().iteritems():

            # First we set the preference members
            meta = member.metadata
            if meta and 'pref' in meta:
                if name not in config:
                    continue

                # member_from_str handle containers
                value = config[name]
                validated = member_from_str(member, value)

                setattr(task, name, validated)

            # Then we deal with the child tasks
            elif meta and 'child' in meta:
                if isinstance(member, (ContainerList, List)):
                    i = 0
                    pref = name + '_{}'
                    validated = []
                    while True:
                        child_name = pref.format(i)
                        if child_name not in config:
                            break
                        child_config = config[child_name]
                        child_class_name = child_config.pop('task_class')
                        child_class = dependencies['tasks'][child_class_name]
                        child = child_class.build_from_config(child_config,
                                                              dependencies)
                        validated.append(child)
                        i += 1

                else:
                    if name not in config:
                        continue
                    child_config = config[name]
                    child_class_name = child_config.pop('task_class')
                    child_class = dependencies['tasks'][child_class_name]
                    validated = child_class.build_from_config(child_config,
                                                              dependencies)

                setattr(task, name, validated)

        return task

    # --- Private API ---------------------------------------------------------

    #: Last removed child and list of database access exceptions attached to
    #: it and necessity to observe its _access_exs.
    _last_removed = Tuple(default=(None, None, False))

    #: Last access exceptions desactivayed from a child.
    _last_exs = Coerced(set)

    #: List of access_exs, linked to access exs in child, disabled because
    #: child disabled some access_exs.
    _disabled_exs = List()

    # @observe('task_name, task_path, task_depth')
    def _update_paths(self, change):
        """Takes care that the paths, the database and the task names remains
        coherent.

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

    def _gather_children_task(self):
        """ Build a flat list of all children task.

        The children_task tasks are garanteed to always appear last in that
        list.

        """
        children = []
        for name in tagged_members(self, 'child'):
            if name == 'children_task':
                continue

            child = getattr(self, name)
            if child:
                if isinstance(child, list):
                    children.extend(child)
                else:
                    children.append(child)

        children.extend(self.children_task)

        return children

    def _observe_children_task(self, change):
        """Handle children being added or removed from the task.

        """
        # Do nothing in the absence of a root task.
        if self.has_root:
            # The whole list changed.
            if change['type'] == 'update':
                added = set(change['value']) - set(change['oldvalue'])
                removed = set(change['oldvalue']) - set(change['value'])
                for child in removed:
                    self._child_removed(child)
                for child in added:
                    self._child_added(child)

            # An operation has been performed on the list.
            elif change['type'] == 'container':
                op = change['operation']

                # Children have been added
                if op in ('__iadd__', 'append', 'extend', 'insert'):
                    if 'item' in change:
                        self._child_added(change['item'])
                    if 'items' in change:
                        for child in change['items']:
                            self._child_added(child)

                # Children have been removed.
                elif op in ('__delitem__', 'remove', 'pop'):
                    if 'item' in change:
                        self._child_removed(change['item'])
                    if 'items' in change:
                        for child in change['items']:
                            self._child_removed(child)

                # One child was replaced.
                elif op in ('__setitem__',):
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

    def _child_added(self, child):
        """Update the database, depth and preferences when a child is added.

        """
        child.task_depth = self.task_depth + 1
        child.task_database = self.task_database
        child.task_path = self.task_path + '/' + self.task_name

        # Give him its root so that it can proceed to any child
        # registration it needs to.
        child.root_task = self.root_task
        child.parent_task = self

        # Ask the child to register in database
        child.register_in_database()
        # Register anew preferences to keep the right ordering for the childs
        self.register_preferences()

        if child is self._last_removed[0]:
            entries = self._last_removed[1]
            self._refresh_access_exceptions(entries,
                                            child=child,
                                            observer=self._last_removed[2])
            access_ex = self.access_exs[:]
            access_ex.extend(entries)
            self.access_exs = access_ex

        self._last_removed = (None, None, False)

    def _child_removed(self, child):
        """Update the database, depth and preferences when a child is removed.

        """
        # List all the task database entries associated with the child just
        # removed.
        access_obs = False
        data_entries = [child.task_name + '_' + entry
                        for entry in child.task_database_entries]

        # Take access exceptions into account for ComplexTask and remove
        # observer if any.
        if isinstance(child, ComplexTask):
            data_entries += child.access_exs
            access_obs = child.has_observer('access_exs',
                                            self._child_access_exs_changed)
            if access_obs:
                child.unobserve('access_exs',
                                self._child_access_exs_changed)

        # Update preferences, cleanup database
        self.register_preferences()
        child.unregister_from_database()
        child.root_task = None
        child.parent_task = None

        # Remove all access exception linked to that child from
        # exceptions.
        access_exs = self.access_exs[:]
        sus_access_exs = [ex for ex in access_exs if ex in data_entries]
        self._refresh_access_exceptions(removed=sus_access_exs, child=child,
                                        observer=access_obs)
        for ex in sus_access_exs:
            access_exs.remove(ex)
        self.access_exs = access_exs

        # Keep list of exceptions to restore them if child is re-added.
        # This avoids screwing up access exceptions when moving a task.
        if sus_access_exs:
            self._last_removed = (child, sus_access_exs, access_obs)

    def _observe_root_task(self, change):
        """ Observer.

        Make sure that all children get all the info they need to behave
        correctly when the task get its root parent (ie the task is now
        in a 'correct' environnement).

        """
        if change['value'] is None:
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

                        # Give it its root so that it can proceed to any child
                        # registration it needs to.
                        aux.parent_task = self
                        aux.root_task = self.root_task

                else:
                    child.task_depth = self.task_depth + 1
                    child.task_database = self.task_database
                    child.task_path = self.task_path + '/' + self.task_name

                    # Give him its root so that it can proceed to any child
                    # registration it needs to.
                    child.parent_task = self
                    child.root_task = self.root_task

    def _refresh_access_exceptions(self, added=[], removed=[], child=None,
                                   observer=False):
        """ Refresh the database access exceptions.

        This method leave the access_exs attribute unchanged it is the
        responsability of the caller to update it.

        Parameters
        ----------
        added : list, optional
            List of database access exceptions to add to the database.

        removed : list, optional
            List of database access exceptions to remove from the database.

        child : BaseTask, optional
            Child task declaring the database entries. If provided all database
            entries will be assumed to be declared by this child.

        """
        if not added and not removed:
            added = self.access_exs

        database = self.task_database
        ex_path = self.task_path
        if added:
            for entry in added:
                # If a child is provided assume it is the one declaring the
                # entry.
                if child and observer:
                    database.add_access_exception(ex_path,
                                                  entry, self.task_path)
                    child.observe('access_exs', self._child_access_exs_changed)
                elif child:
                    database.add_access_exception(ex_path,
                                                  entry, child.task_path)

                # Find the child declaring the entry to determine if the
                # entry is an access exception.
                else:
                    for child in self._gather_children_task():
                        entries = [child.task_name + '_' + e
                                   for e in child.task_database_entries]
                        if entry in entries:
                            database.add_access_exception(ex_path,
                                                          entry,
                                                          child.task_path)

                        elif hasattr(child, 'access_exs') and\
                                entry in child.access_exs:
                            database.add_access_exception(ex_path,
                                                          entry,
                                                          child.task_path)
                            child.observe('access_exs',
                                          self._child_access_exs_changed)

        else:
            for entry in removed:
                # Check that the entry is known.
                if entry not in self.access_exs:
                    err = 'No access exeption for entry {} in {}.'
                    raise KeyError(err.format(entry, self.task_name))

                # If a child is provided assume it is the one declaring the
                # entry.
                if child and observer:
                    database.remove_access_exception(ex_path,
                                                     entry)
                    child.unobserve('access_exs',
                                    self._child_access_exs_changed)
                elif child:
                    database.remove_access_exception(ex_path,
                                                     entry)

                # Find the child declaring the entry to determine if the
                # entry is an access exception.
                else:
                    for child in self._gather_children_task():
                        entries = [child.task_name + '_' + e
                                   for e in child.task_database_entries]
                        if entry in entries:
                            database.remove_access_exception(ex_path,
                                                             entry)

                        elif hasattr(child, 'access_exs') and\
                                entry in child.access_exs:
                            database.remove_access_exception(ex_path,
                                                             entry)
                            child.unobserve('access_exs',
                                            self._child_access_exs_changed)

    def _child_access_exs_changed(self, change):
        """ Observer connected to ComplexTask children to watch their
        access_exs.

        """
        if change['type'] == 'update':
            added = set(change['value']) - set(change.get('oldvalue', []))
            removed = set(change.get('oldvalue', [])) - set(change['value'])

        elif change['type'] == 'container':
            op = change['operation']
            if op in ('__iadd__', 'append', 'extend', 'insert'):
                if 'item' in change:
                    added = set([change['item']])
                if 'items' in change:
                    added = set(change['items'])
                removed = set()

            elif op in ('__delitem__', 'remove', 'pop'):
                if 'item' in change:
                    removed = set([change['item']])
                if 'items' in change:
                    removed = set(change['items'])
                added = set()

        if added and self._last_exs == added:
            self._refresh_access_exceptions(added, child=change['object'],
                                            observer=False)
            self.access_exs.extend(added)
            self._last_exs = []

        if removed:
            sus_access_exs = [ex for ex in removed
                              if ex in self.access_exs]
            if sus_access_exs:
                self._refresh_access_exceptions(removed=sus_access_exs,
                                                child=change['object'],
                                                observer=False)
                access_exs = self.access_exs[:]
                for ex in sus_access_exs:
                    access_exs.remove(ex)
                self.access_exs = access_exs
                self._last_exs = removed

        else:
            change['object'].unobserve('access_exs',
                                       self._child_access_exs_changed)


from multiprocessing.synchronize import Event
from threading import Event as tEvent


class RootTask(ComplexTask):
    """Special task which is always the root of a measurement.

    On this class and this class only perform can and should be called
    directly.

    """
    # --- Public API ----------------------------------------------------------

    #: Path to which log infos, preferences, etc should be written by default.
    default_path = Unicode('').tag(pref=True)

    #: Header assembled just before the measure is run.
    default_header = Str('')

    #: ID of the measurement. This could be a number that will appear in files
    meas_id = Str('')

    #: Description of the measurement.
    meas_decription = Str('')

    #: Date at which the measurement occured.
    meas_date = Str('')

    #: Dict storing data needed at execution time (ex: drivers classes)
    run_time = Dict()

    #: Inter-process event signaling the task it should stop execution.
    should_stop = Instance(Event)

    #: Inter-process event signaling the task it should pause execution.
    should_pause = Instance(Event)

    #: Inter-process event signaling the task is paused.
    paused = Instance(Event)

    #: Inter-Thread event signaling the main thread is done, handling the
    #: measure resuming.
    resume = Value()

    #: Dict like object used to store references to all running threads.
    #: Keys are pools ids, values list of threads. Keys are never deleted.
    threads = Typed(SharedDict, (list,))

    #: Dict like object used to store references to used instruments.
    #: Keys are instrument profile names, values instr instance. Keys are never
    #: deleted.
    instrs = Typed(SharedDict, ())

    #: Dict like object used to store file handle.
    #: Keys are file handle id as defined by the first user of the file.
    #: Keys can be deleted.
    files = Typed(SharedDict, ())

    #: Counter keeping track of the active threads.
    active_threads_counter = Typed(SharedCounter, kwargs={'count': 1})

    #: Counter keeping track of the paused threads.
    paused_threads_counter = Typed(SharedCounter, ())

    # Setting default values for the root task.
    has_root = set_default(True)
    task_name = set_default('Root')
    task_label = set_default('Root')
    task_depth = set_default(0)
    task_path = set_default('root')
    task_database_entries = set_default({'default_path': '', 'meas_id': '',
                                             'meas_decription': '',
                                             'meas_date': ''})

    def __init__(self, *args, **kwargs):
        self.task_preferences = ConfigObj(indent_type='    ')
        self.task_database = TaskDatabase()
        super(RootTask, self).__init__(*args, **kwargs)
        self.register_in_database()
        self.root_task = self
        self.parent_task = self

    def check(self, *args, **kwargs):
        traceback = {}
        test = True
        if not os.path.isdir(self.default_path):
            test = False
            traceback[self.task_path + '/' + self.task_name] =\
                'The provided default path is not a valid directory'
        self.task_database.set_value('root', 'default_path', self.default_path)
        self.meas_date = (str(datetime.datetime.now()).split(' '))[0]
        check = super(RootTask, self).check(*args, **kwargs)
        test = test and check[0]
        traceback.update(check[1])
        return test, traceback

    @smooth_crash
    def perform(self):
        """ Run sequentially all child tasks, and close ressources.

        """
        try:
            for child in self.children_task:
                child.perform_(child)
        except Exception:
            log = logging.getLogger(__name__)
            mes = 'The following unhandled exception occured:'
            log.exception(mes)
            self.should_stop.set()
        finally:
            # Wait for all threads to terminate.
            for pool_name in self.threads:
                with self.threads.safe_access(pool_name) as pool:
                    for thread in pool:
                        try:
                            thread.join()
                        except Exception:
                            log = logging.getLogger(__name__)
                            mes = 'Failed to close join thread:'
                            log.exception(mes)

            # Close connection to all instruments.
            instrs = self.instrs
            for instr_profile in instrs:
                try:
                    instrs[instr_profile].close_connection()
                except Exception:
                    log = logging.getLogger(__name__)
                    mes = 'Failed to close connection to instr:'
                    log.exception(mes)

            # Close all opened files.
            files = self.files
            for file_id in files:
                try:
                    files[file_id].close()
                except Exception:
                    log = logging.getLogger(__name__)
                    mes = 'Failed to close file handler:'
                    log.exception(mes)

    def register_in_database(self):
        """ Create a node in the database and register all entries.

        This method registers both the task entries and all the tasks tagged
        as child.

        """
        if self.task_database_entries:
            for entry in self.task_database_entries:
                # Perform a deepcopy of the entry value as I don't want to
                # alter that default value when dealing with the database later
                # on (apply for list and dict).
                value = deepcopy(self.task_database_entries[entry])
                self.task_database.set_value(self.task_path,
                                             entry,
                                             value)

        self.task_database.create_node(self.task_path, self.task_name)

        # ComplexTask defines children_task so we always get something
        for name in tagged_members(self, 'child'):
            child = getattr(self, name)
            if child:
                if isinstance(child, list):
                    for aux in child:
                        aux.register_in_database()
                else:
                    child.register_in_database()

    # --- Private API ---------------------------------------------------------

    # Overrided here to give the child its root task right away.
    def _child_added(self, child):
        # Give the child all the info it needs to register
        child.task_depth = self.task_depth + 1
        child.task_database = self.task_database
        child.task_path = self.task_path

        # Give him its root so that it can proceed to any child
        # registration it needs to.
        child.parent_task = self
        child.root_task = self.root_task

        # Ask the child to register in database
        child.register_in_database()
        # Register anew preferences to keep the right ordering for the childs
        self.register_preferences()

    def _default_task_class(self):
        return ComplexTask.__name__

    def _observe_default_path(self, change):
        """
        """
        new = change['value']
        if new:
            self.default_path = os.path.normpath(new)
            self.task_database.set_value('root', 'default_path',
                                         self.default_path)

    def _observe_task_name(self, change):
        """ Update the label any time the task name changes.

        """
        pass

    @observe('active_threads_counter.count', 'paused_threads_counter.count')
    def _state(self, change):
        """

        """
        p_count = self.paused_threads_counter.count
        a_count = self.active_threads_counter.count
        if a_count == p_count:
            self.paused.set()

        if p_count == 0:
            self.paused.clear()

    def _default_resume(self):
        return tEvent()

KNOWN_PY_TASKS = [ComplexTask]

TASK_PACKAGES = ['tasks_util', 'tasks_logic']
