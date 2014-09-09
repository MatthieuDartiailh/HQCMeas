# -*- coding: utf-8 -*-
# =============================================================================
# module : pulses/base_sequences.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from atom.api import (Int, Instance, Str, Dict, Bool, List,
                      ContainerList, set_default)
from itertools import chain
from inspect import cleandoc

from hqc_meas.utils.atom_util import member_from_str
from .contexts.base_context import BaseContext
from .entry_eval import eval_entry
from .item import Item
from .pulse import Pulse


class Sequence(Item):
    """ A sequence is an ensemble of pulses.

    """
    # --- Public API ----------------------------------------------------------

    #: Name of the sequence (help make a sequence more readable)
    name = Str().tag(pref=True)

    #: List of items this sequence consists of.
    items = ContainerList(Instance(Item))

    #: Dict of variables whose scope is limited to the sequence. Each key/value
    #: pair represents the name and definition of the variable.
    local_vars = Dict(Str()).tag(pref=True)

    #: Bool indicating whether or not the sequence has a hard defined
    #: start/stop/duration. In case it does not the associated values won't
    #: be computed.
    time_constrained = Bool().tag(pref=True)

    def prepare_compilation(self):
        """ Clear all internal caches before compiling anew the sequence.

        """
        self._evaluated_vars = {}
        self._compiled = []
        for i in self.items:
            if isinstance(i, Sequence):
                i.prepare_compilation()

    def compile_sequence(self, root_vars, sequence_locals, missings, errors):
        """ Evaluate the sequence vars and compile the list of pulses.

        Parameters
        ----------
        root_vars : dict
            Dictionary of global variables for the all items. This will
            tipically contains the i_start/stop/duration and the root vars.
            This dict must be updated with global new values but for
            evaluation sequence_locals must be used.

        sequence_locals : dict
            Dictionary of variables whose scope is limited to this sequence
            parent. This dict must be updated with global new values and
            must be used to perform evaluation (It always contains all the
            names defined in root_vars).

        missings : set
            Set of unfound local variables.

        errors : dict
            Dict of the errors which happened when performing the evaluation.

        Returns
        -------
        flag : bool
            Boolean indicating whether or not the evaluation succeeded.

        pulses : list
            List of pulses in which all the string entries have been evaluated.

        """
        prefix = '{}_'.format(self.index)

        # Definition evaluation.
        if self.time_constrained:
            self.eval_entries(root_vars, sequence_locals, missings, errors)

        # Local vars computation.
        for name, formula in self.local_vars.iteritems():
            if name not in self._evaluated_vars:
                try:
                    val = eval_entry(formula, sequence_locals, missings)
                    self._evaluated_vars[name] = val
                except Exception as e:
                    errors[prefix + name] = repr(e)

        local_namespace = sequence_locals.copy()
        local_namespace.update(self._evaluated_vars)

        res, pulses = self._compile_items(root_vars, local_namespace,
                                          missings, errors)

        if res:
            if self.time_constrained:
                # Check if start, stop and duration of sequence are compatible.
                start_err = [pulse for pulse in pulses
                             if pulse.start < self.start]
                stop_err = [pulse for pulse in pulses
                            if pulse.stop > self.stop]

                if start_err:
                    mess = cleandoc('''The start time of the following items {}
                        is smaller than the start time of the sequence {}''')
                    mess = mess.replace('\n', ' ')
                    ind = [p.index for p in start_err]
                    errors[self.name + '-start'] = mess.format(ind, self.index)
                if stop_err:
                    mess = cleandoc('''The stop time of the following items {}
                        is larger than the stop time of the sequence {}''')
                    mess = mess.replace('\n', ' ')
                    ind = [p.index for p in stop_err]
                    errors[self.name + '-stop'] = mess.format(ind, self.index)

                if errors:
                    return False, []

            return True, pulses

        else:
            return False, []

    def get_bindable_vars(self):
        """ Access the list of bindable vars for the sequence.

        """
        return self.local_vars.keys() + self.parent.get_bindable_vars()

    def walk(self, members, callables):
        """ Explore the items hierarchy.

        Missing values will be filled with None.

        Parameters
        ----------
        members : list(str)
            Names of the members whose value should be retrieved.

        callables : dict(callable)
            Dict {name: callables} to call on every item in the hierarchy. Each
            callable should take as single argument the task.

        Returns
        -------
        answer : list
            List summarizing the result of the exploration.

        """
        answer = [self._answer(members, callables)]
        for item in self.items:
            if isinstance(item, Pulse):
                answer.append(item._answer(members, callables))
            else:
                answer.append(item.walk(members, callables))

        return answer

    def preferences_from_members(self):
        """ Get the members values as string to store them in .ini files.

        Reimplemented here to save items.

        """
        pref = super(Sequence, self).preferences_from_members()

        for i, item in enumerate(self.items):
            pref['item_{}'.format(i)] = item.preferences_from_members()

        return pref

    def update_members_from_preferences(self, **parameters):
        """ Use the string values given in the parameters to update the members

        This function will call itself on any tagged HasPrefAtom member.
        Reimplemented here to update items.

        """
        super(Sequence, self).update_members_from_preferences(**parameters)

        for i, item in enumerate(self.items):
            para = parameters['item_{}'.format(i)]
            item.update_members_from_preferences(**para)

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

        Returns
        -------
        sequence : Sequence
            Newly created and initiliazed sequence.

        Notes
        -----
        This method is fairly powerful and can handle a lot of cases so
        don't override it without checking that it works.

        """
        sequence = cls()
        for name, member in sequence.members().iteritems():

            # First we set the preference members
            meta = member.metadata
            if meta and 'pref' in meta:
                if name not in config:
                    continue

                # member_from_str handle containers
                value = config[name]
                validated = member_from_str(member, value)

                setattr(sequence, name, validated)

        i = 0
        pref = 'item_{}'
        validated = []
        while True:
            item_name = pref.format(i)
            if item_name not in config:
                break
            item_config = config[item_name]
            item_class_name = item_config.pop('item_class')
            item_class = dependencies['pulses'][item_class_name]
            item = item_class.build_from_config(item_config,
                                                dependencies)
            validated.append(item)
            i += 1

        setattr(sequence, 'items', validated)

        return sequence

    # --- Private API ---------------------------------------------------------

    #: Last index used by the sequence.
    _last_index = Int()

    #: Dict of all already evaluated vars.
    _evaluated_vars = Dict()

    #: List of already compiled items.
    _compiled = List()

    def _compile_items(self, root_vars, sequence_locals, missings, errors):
        """ Compile the sequence in a flat list of pulses.

        Parameters
        ----------
        root_vars : dict
            Dictionary of global variables for the all items. This will
            tipically contains the i_start/stop/duration and the root vars.

        sequence_locals : dict
            Dictionary of variables whose scope is limited to this sequence.

        missings : set
            Set of unfound local variables.

        errors : dict
            Dict of the errors which happened when performing the evaluation.

        Returns
        -------
        flag : bool
            Boolean indicating whether or not the evaluation succeeded.

        pulses : list
            List of pulses in which all the string entries have been evaluated.

        """
        # Inplace modification of compile will update self._compiled.
        if not self._compiled:
            self._compiled = [None for i in self.items if i.enabled]
        compiled = self._compiled

        # Compilation of items in multiple passes.
        while True:
            miss = set()

            index = -1
            for item in self.items:
                # Skip disabled items
                if not item.enabled:
                    continue

                # Increment index so that we set the right object in compiled.
                index += 1

                # Skip evaluation if object has already been compiled.
                if compiled[index] is not None:
                    continue

                # If we get a pulse simply evaluate the entries, to add their
                # values to the locals and keep track of the missings to now
                # when to abort compilation.
                if isinstance(item, Pulse):
                    success = item.eval_entries(root_vars, sequence_locals,
                                                miss, errors)
                    if success:
                        compiled[index] = [item]

                # Here we got a sequence so we must try to compile it.
                else:
                    success, items = item.compile_sequence(root_vars,
                                                           sequence_locals,
                                                           miss, errors)
                    if success:
                        compiled[index] = items

            known_locals = set(sequence_locals.keys())
            # If none of the variables found missing during last pass is now
            # known stop compilation as we now reached a dead end. Same if an
            # error occured.
            if errors or miss and (not known_locals & miss):
                # Update the missings given by caller so that it knows it this
                # failure is linked to circle references.
                missings.update(miss)
                return False, []

            # If no var was found missing during last pass (and as no error
            # occured) it means the compilation succeeded.
            elif not miss:
                pulses = list(chain.from_iterable(compiled))
                return True, pulses

    def _answer(self, members, callables):
        """ Collect answers for the walk method.

        """
        answers = {m: getattr(self, m, None) for m in members}
        answers.update({k: c(self) for k, c in callables.iteritems()})
        return answers

    def _observe_root(self, change):
        """ Observer passing the root to all children.

        This allow to build a sequence without a root and parent it later.

        """
        if change['value']:
            for item in self.items:
                item.root = self.root
                if isinstance(item, Sequence):
                    item.observe('_last_index', self._item_last_index_updated)
                    item.parent = self
            # Connect only now to avoid cleaning up in an unwanted way the
            # root linkable vars attr.
            self.observe('items', self._items_updated)

        else:
            self.unobserve('items', self._items_updated)
            for item in self.items:
                item.root = None
                if isinstance(item, Sequence):
                    item.unobserve('_last_index',
                                   self._item_last_index_updated)
            self.observe('items', self._items_updated)

    def _observe_time_constrained(self, change):
        """

        """
        if change['value']:
            self.linkable_vars = ['start', 'stop', 'duration']
        else:
            self.linkable_vars = []

    def _items_updated(self, change):
        """ Observer for the items list.

        """
        if self.root:
            # The whole list changed.
            if change['type'] == 'update':
                added = set(change['value']) - set(change['oldvalue'])
                removed = set(change['oldvalue']) - set(change['value'])
                for item in removed:
                    self._item_removed(item)
                for item in added:
                    self._item_added(item)

            # An operation has been performed on the list.
            elif change['type'] == 'container':
                op = change['operation']

                # itemren have been added
                if op in ('__iadd__', 'append', 'extend', 'insert'):
                    if 'item' in change:
                        self._item_added(change['item'])
                    if 'items' in change:
                        for item in change['items']:
                            self._item_added(item)

                # itemren have been removed.
                elif op in ('__delitem__', 'remove', 'pop'):
                    if 'item' in change:
                        self._item_removed(change['item'])
                    if 'items' in change:
                        for item in change['items']:
                            self._item_removed(item)

                # One item was replaced.
                elif op in ('__setitem__'):
                    old = change['olditem']
                    if isinstance(old, list):
                        for item in old:
                            self._item_removed(item)
                    else:
                        self._item_removed(old)

                    new = change['newitem']
                    if isinstance(new, list):
                        for item in new:
                            self._item_added(item)
                    else:
                        self._item_added(new)

            self._recompute_indexes()

    def _item_added(self, item):
        """ Fill in the attributes of a newly added item.

        """
        item.root = self.root
        item.parent = self
        item.observe('linkable_vars', self.root._update_linkable_vars)
        if isinstance(item, Sequence):
            item.observe('_last_index', self._item_last_index_updated)

    def _item_removed(self, item):
        """ Clear the attributes of a removed item.

        """
        item.unobserve('linkable_vars', self.root._update_linkable_vars)
        del item.root
        del item.parent
        item.index = 0
        if isinstance(item, Sequence):
            item.unobserve('_last_index', self._item_last_index_updated)

    def _recompute_indexes(self, first_index=0, free_index=None):
        """ Recompute the item indexes and update the vars of the root_seq.

        Parameters
        ----------
        first_index : int, optional
            Index in items of the first item whose index needs to be updated.

        free_index : int, optional
            Value of the first free index.

        """
        if free_index is None:
            free_index = self.index + 1

        # Cleanup the linkable_vars for all the pulses which will be reindexed.
        linked_vars = self.root.linkable_vars
        for var in linked_vars[:]:
            if var[0].isdigit() and int(var[0]) >= free_index:
                linked_vars.remove(var)

        for item in self.items[first_index:]:

            item.index = free_index
            prefix = '{}_'.format(free_index)
            linkable_vars = [prefix + var for var in item.linkable_vars]
            linked_vars.extend(linkable_vars)

            if isinstance(item, Pulse):
                free_index += 1

            # We have a sequence.
            else:
                item.unobserve('_last_index', self._item_last_index_updated)
                item._recompute_indexes()
                item.observe('_last_index', self._item_last_index_updated)
                free_index = item._last_index + 1

        self._last_index = free_index - 1

    def _item_last_index_updated(self, change):
        """ Update the items indexes whenever the last index of a child
        sequence is updated.

        """
        index = self.items.index(change['object']) + 1
        free_index = change['value'] + 1
        self._recompute_indexes(index, free_index)


class RootSequence(Sequence):
    """ Base of any pulse sequences.

    This Item perform the first step of compilation by evaluating all the
    entries and then unravelling the pulse sequence (elimination of condition
    and loop flattening).

    Notes
    -----

    The linkable_vars of the RootSequence stores all the known linkable vars
    for the sequence.
    The local_vars of the RootSequence acts as global variables and are not
    evaluated.
    The start, stop, duration and def_1, def_2 members are not used by the
    RootSequence. The time_constrained member only affects the use of the
    sequence duration.

    """
    # --- Public API ----------------------------------------------------------

    #: Duration of the sequence when it is fixed. The unit of this time is
    # fixed by the context.
    sequence_duration = Str().tag(pref=True)

    #: Reference to the executioner context of the sequence.
    context = Instance(BaseContext)

    index = set_default(0)
    name = set_default('Root')

    def __init__(self, **kwargs):
        """

        """
        super(RootSequence, self).__init__(**kwargs)
        self.root = self

    def compile_sequence(self, use_context=True):
        """ Compile a sequence to useful format.

        Parameters
        ---------------
        use_context : bool, optional
            Should the context compile the pulse sequence.

        Returns
        -----------
        result : bool
            Flag indicating whether or not the compilation succeeded.

        args : iterable
            Objects depending on the result and use_context flag.
            In case of failure: tuple
                - a set of the entries whose values where never found and a
                dict of the errors which occured during compilation.
            In case of success:
                - a flat list of Pulse if use_context is False
                - a context dependent result otherwise.

        """
        missings = set()
        errors = {}
        root_vars = self.local_vars.copy()

        if self.time_constrained:
            try:
                duration = eval_entry(self.sequence_duration, root_vars,
                                      missings)
                root_vars['sequence_end'] = duration
            except Exception as e:
                errors['root_seq_duration'] = repr(e)

        res, pulses = self._compile_items(root_vars, root_vars,
                                          missings, errors)

        if not res:
            return False, (missings, errors)

        if self.time_constrained:
            err = [p for p in pulses if p.stop > duration]

            if err:
                mess = cleandoc('''The stop time of the following pulses {}
                        is larger than the duration of the sequence.''')
                ind = [p.index for p in err]
                errors['Root-stop'] = mess.format(ind)
                return False, (missings, errors)

        if not use_context:
            return True, pulses

        else:
            kwargs = {}
            if self.time_constrained:
                kwargs['sequence_duration'] = duration
            return self.context.compile_sequence(pulses, **kwargs)

    def get_bindable_vars(self):
        """ Access the list of bindable vars for the sequence.

        """
        return self.linkable_vars + self.local_vars.keys()

    def preferences_from_members(self):
        """ Get the members values as string to store them in .ini files.

        Reimplemented here to save context.

        """
        pref = super(RootSequence, self).preferences_from_members()

        pref['context'] = self.context.preferences_from_members()

        return pref

    def update_members_from_preferences(self, **parameters):
        """ Use the string values given in the parameters to update the members

        This function will call itself on any tagged HasPrefAtom member.
        Reimplemented here to update context.

        """
        super(RootSequence, self).update_members_from_preferences(**parameters)

        para = parameters['context']
        self.context.update_members_from_preferences(**para)

    @classmethod
    def build_from_config(cls, config, dependencies):
        """ Create a new instance using the provided infos for initialisation.

        Overridden here to allow context creation.

        Parameters
        ----------
        config : dict(str)
            Dictionary holding the new values to give to the members in string
            format, or dictionnary like for instance with prefs.

        dependencies : dict
            Dictionary holding the necessary classes needed when rebuilding.

        Returns
        -------
        sequence : Sequence
            Newly created and initiliazed sequence.

        """
        context_config = config['context']
        context_class_name = context_config.pop('context_class')
        context_class = dependencies['pulses']['contexts'][context_class_name]
        context = context_class()
        context.update_members_from_preferences(**context_config)
        config['context'] = context
        return super(RootSequence, cls).build_from_config(config,
                                                          dependencies)

    # --- Private API ---------------------------------------------------------

    def _answer(self, members, callables):
        """

        """
        answers = super(RootSequence, self)._answer(members, callables)
        con_members = [m for m in members
                       if m.startswith('context.')]
        answers.update({m: getattr(self.context, m[8:], None)
                        for m in con_members})

        return answers

    def _observe_time_constrained(self, change):
        """ Keep the linkable_vars list in sync with fix_sequence_duration.

        """
        if change['value']:
            link_vars = self.linkable_vars[:]
            link_vars.insert(0, 'sequence_end')
            self.linkable_vars = link_vars
        elif 'sequence_end' in self.linkable_vars:
            link_vars = self.linkable_vars[:]
            link_vars.remove('sequence_end')
            self.linkable_vars = link_vars

    def _update_linkable_vars(self, change):
        """
        """
        # Don't won't this to happen on member init.
        if change['type'] == 'update':
            link_vars = self.linkable_vars
            item = change['object']
            prefix = '{}_{{}}'.format(item.index)
            added = set(change['value']) - set(change.get('oldvalue', []))
            removed = set(change.get('oldvalue', [])) - set(change['value'])
            link_vars.extend([prefix.format(var)
                              for var in added])
            for var in removed:
                r = prefix.format(var)
                if r in link_vars:
                    link_vars.remove(r)
