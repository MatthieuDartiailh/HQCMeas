# -*- coding: utf-8 -*-
#==============================================================================
# module : pulses.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import (Int, Instance, Str, Enum, Float, Dict, List, Typed, Bool,
                      ContainerList, ForwardInstance, ForwardTyped,
                      set_default)
from itertools import chain

from hqc_meas.utils.atom_util import HasPrefAtom
from .contexts.base_context import BaseContext
from .shape.base_shapes import AbstractShape
from .shape.modulation import Modulation
from .entry_eval import eval_entry


class Item(HasPrefAtom):
    """ Base component a pulse sequence.

    """
    #: Index identifying the item inside the sequence.
    index = Int()

    #: Reference to the executioner context of the item.
    context = Instance(BaseContext)

    #: Flag to disable a particular item.
    enabled = Bool(True).tag(pref=True)

    #: Class of the item to use when rebuilding a sequence.
    item_class = Str().tag(pref=True)

    #: Name of the variable which can be referenced in other items.
    linkable_vars = List()

    #: Reference to the root sequence.
    root = ForwardTyped(lambda: RootSequence)

    def _default_item_class(self):
        """ Default value for the item_class member.

        """
        return self.__class__.__name__


class Pulse(Item):
    """ Represent a pulse to perfom during a sequence.

    """
    #: The kind of pulse can be either logical or ananlogical.
    kind = Enum('logical', 'analogical').tag(pref=True)

    #: Channel of the executioner which should perfom the pulse.
    channel = Str().tag(pref=True)

    #: Mode defining how the def_1 and def_2 attrs shiould be interpreted.
    def_mode = Enum('Start/Stop',
                    'Start/Duration',
                    'Duration/Stop').tag(pref=True)

    #: String representing the pulse first element of definition : according
    #: to the selected mode it evaluated value will either be used for the
    #: start instant, or duration of the pulse.
    def_1 = Str().tag(pref=True)

    #: String representing the pulse second element of definition : according
    #: to the selected mode it evaluated value will either be used for the
    #: duration, or stop instant of the pulse.
    def_2 = Str().tag(pref=True)

    linkable_vars = set_default(['start', 'stop', 'duration'])

    #: Actual start instant of the pulse with respect to the beginning of the
    #: sequence. The unit of this time depends of the setting of the context.
    start = Float()

    #: Actual duration of the pulse. The unit of this time depends of the
    #: setting of the context.
    duration = Float()

    #: Actual stop instant of the pulse with respect to the beginning of the
    #: sequence. The unit of this time depends of the setting of the context.
    stop = Float()

    #: Modulation to apply to the pulse. Only enabled in analogical mode.
    modulation = Typed(Modulation, ()).tag(pref=True)

    #: Shape of the pulse. Only enabled in analogical mode.
    shape = Instance(AbstractShape).tag(pref=True)

    def eval_entries(self, sequence_locals, missings, errors):
        """
        """
        # Name of the parameter which will be evaluated.
        par1 = self.def_mode.split('/')[0].lower()
        par2 = self.def_mode.split('/')[1].lower()
        prefix = '{}_'.format(self.index)
        
        # Evaluation of the first parameter.
        d1 = None
        try:
            d1 = eval_entry(self.def_1, sequence_locals, missings)
        except Exception as e:
            errors[prefix + par1] = repr(e)
            
        if d1 is not None:
            setattr(self, par1, d1)
            sequence_locals[prefix + par1] = d1

        # Evaluation of the second parameter.
        d2 = None
        try:
            d2 = eval_entry(self.def_2, sequence_locals, missings)
        except Exception as e:
            errors[prefix + par2] = repr(e)
            
        if d2 is not None:
            setattr(self, par2, d2)
            sequence_locals[prefix + par2] = d2
         
         # Computation of the third.
        success = d1 is not None and d2 is not None
        if success:
            if self.def_mode == 'Start/Duration':
                 self.stop = d1 + d2
                 sequence_locals[prefix + 'stop'] = self.stop
            elif self.def_mode == 'Start/Stop':
                self.duration = d2 - d1
                sequence_locals[prefix + 'duration'] = self.stop
            else:
                self.start = d2 - d1
                sequence_locals[prefix + 'start'] = self.stop
         
        if self.kind == 'analogical':
            success &= self.modulation.eval_entries(sequence_locals, missings, errors, self.index)
            
            success &= self.shape.eval_entries(sequence_locals, missings, errors, self.index)
            
        return success

    def compute(self, time):
        """ Compute the relative strength of the pulse at a given time.

        """
        if self.start <= time <= self.stop:
            if self.kind == 'analogical':
                mod = self.modulation.compute(time, self.context.time_unit)
                shape = self.shape.compute(time, self.context.time_unit)
                return mod*shape
            else:
                return 1

        else:
            return 0
            
#    def update_members_from_preferences():
#        """
#        """
#        NO #recreate shape before loading preferences if it makes senses
#        
#        # Shape should be created by the loader.


class Sequence(Item):
    """ A sequence is an ensemble of pulses.

    """
    #--- Public API -----------------------------------------------------------

    #: List of items this sequence consists of.
    items = ContainerList(Instance(Item))

    #: Parent sequence of this sequence.
    parent = ForwardInstance(lambda: Sequence)
    
    def compile_sequence(self, sequence_locals, missing_locals, errors):
        """
        
        """
        compiled = [None for i in xrange(len(self.items))]
        while True:
            missings = set()            
            
            for i, item in enumerate(self.items):
                # If we get a pulse simply evaluate the entries, to add their values to the locals
                # and keep track of the missings to now when to abort compilation.
                if isinstance(item, Pulse):
                    success = item.eval_entries(sequence_locals, missings, errors)
                    if success:
                        compiled[i] = [item]

                # Here we got a sequence so we must try to compile it.                        
                else:
                    success, items = item.compile_sequence(sequence_locals, missings, errors)
                    if success:
                        compiled[i] = items
                        
            known_locals = set(sequence_locals.keys())
            # If none of the variables found missing during last pass is now known stop compilation
            # as we now reached a dead end. Same if an error occured.
            if errors or not known_locals & missings:
                # Update the missings given by caller so that it knows it this failure is linked to circle
                # references.
                missing_locals.update(missings)
                return False, []
                
            # If no var was found missing during last pass (and as no error occured) it means
            # the compilation succeeded.
            elif not missings:
                return True, list(chain.from_iterable(compiled))
                
    def walk(self, members, callables):
        """ Explore the items hierarchy looking.

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
        answer = [self._answer(self, members, callables)]
        for item in self.items:
            if isinstance(item, Pulse):
                answer.append(self._answer(item, members, callables))
            else:
                answer.append(item.walk(members, callables))

        return answer

    #--- Private API ----------------------------------------------------------

    #: Last index used by the sequence.
    _last_index = Int()

    @staticmethod
    def _answer(obj, members, callables):
        """ Collect answers for the walk method.

        """
        answers = {m: getattr(obj, m, None) for m in members}
        answers.update({k: c(obj) for k, c in callables.iteritems()})
        return answers

    def _observe_items(self, change):
        """ Observer for the items list.

        """
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
        """
        """
        item.context = self.context
        if isinstance(item, Sequence):
            item.observe('_last_index', self._item_last_index_updated)
            item.parent = self

    def _item_removed(self, item):
        """
        """
        if isinstance(item, Sequence):
            item.unobserve('_last_index', self._item_last_index_updated)
            del item.parent

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

        for item in self.items[first_index:]:

            linked_vars = self.root.linkable_vars
            for var in item.linkable_vars:
                linked_vars.remove('{}_'.format(item.index) + var)

            item.index = free_index
            prefix = '{}_'.format(item.index)
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


class ConditionalSequence(Sequence):
    """ Sequence whose child items will be included only if a condition is met.

    """
    condition = Str().tag(pref=True)

    linkable_vars = set_default(['condition'])

    def compile_sequence(self, sequence_locals, missing_locals, errors):
        """
        
        """
        cond = None
        try:
            cond = eval_entry(self.condition, sequence_locals, missing_locals)
        except Exception as e:
            errors['{}'.format(self.index) + 'condition'] = repr(e)
            
        if cond is None:
            return False, []
            
        local = '{}'.format(self.index) + 'condition'
        sequence_locals[local] = cond

        if cond:
            return super(ConditionalSequence, self).compile_sequence(sequence_locals,
                                                                                              missing_locals)
                                                                                              
        else:
            return True, []


class RepeatSequence(Sequence):
    """ Sequence whose child items will be included multiple times.

    """
    iter_duration = Str().tag(pref=True)

    iter_number = Str().tag(pref=True)

    linkable_vars = set_default(['iter_start', 'iter_stop'])

    def compile_sequence(self, sequence_locals):
        """
        
        """
        # TODO later will require some use of deepcopy.
        pass


class RootSequence(Sequence):
    """ Base of any pulse sequences.

    This Item perform the first step of compilation by evaluating all the entries and then unravelling
    the pulse sequence (elimination of condition and loop flattening).

    The linkable_vars of the RootSequence stores all the known linkable vars for the sequence.

    """
    #: Dict of external variables.
    external_variables = Dict().tag(pref=True)

    def compile_sequence(self, use_context=True):
        """ Compile a sequence to useful format.
        
        Parameters
        ---------------
        use_context : bool, optional
            Should the context comile the pulse sequence.
            
        Returns
        -----------
        result : bool
            Flag indicating whether or not the compilation succeeded.
            
        *args : 
            Objects depending on the result and use_context flag.
            In case of failure:
                - a set of the entries whose values where never found and a dict of the errors which
                occured during the compilation.
            In case of success:
                - a flat list of Pulse if use_context is false
                - a context dependent result.
        
        """
        sequence_locals = self.external_variables.copy()
        missings = set()
        errors = {}
        
        res, pulses = super(RootSequence, self).compile_sequence(sequence_locals, missings, errors)
        
        if not res:
            return False, missings, errors
            
        elif not use_context:
            return True, pulses
            
        else:
            return self.context.compile_sequence(pulses)