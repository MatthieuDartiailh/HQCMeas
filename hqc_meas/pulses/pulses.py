# -*- coding: utf-8 -*-
#==============================================================================
# module : pulses.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import (Int, Instance, Str, Enum, Float, Dict, List, Typed, Bool,
                      ContainerList, ForwardInstance, ForwardTyped,
                      set_default)

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

    #: Class of the item use when rebuilding a sequence.
    item_class = Str().tag(pref=True)

    #: Name of the variable which can be referenced in other items.
    linkable_vars = List()

    #: Reference to the root sequence.
    root = ForwardTyped(lambda: RootSequence)

    def eval_entries(self, sequence_locals):
        """

        """
        raise NotImplementedError

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

    def eval_entries(self, sequence_locals, missing):
        """
        """
        pass

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


class Sequence(Item):
    """ A sequence is an ensemble of pulses.

    """
    #--- Public API -----------------------------------------------------------

    #: List of items this sequence consists of.
    items = ContainerList(Instance(Item))

    #: Parent sequence of this sequence.
    parent = ForwardInstance(lambda: Sequence)

    def eval_entries(self, sequence_locals):
        """
        """
        pass

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

    def eval_entries(self, sequence_locals):
        """
        """
        pass


class LoopSequence(Sequence):
    """ Sequence whose child items will be included multiple times.

    """
    start = Str().tag(pref=True)

    stop = Str().tag(pref=True)

    step = Str().tag(pref=True)

    linkable_vars = set_default(['index', 'value'])

    def eval_entries(self, sequence_locals):
        """
        """
        pass


class RootSequence(Sequence):
    """ Base of any pulse sequences.

    This Item perform the first step of compilation by evaluating all the
    entries and then unravelling the pulse sequence (elimination of condition
    and loop flattening).

    The linkable_vars of the RootSequence stores all the known linkable vars
    for the sequence.

    """
    #: Dict of external variables.
    external_variables = Dict().tag(pref=True)

    def compile_sequence(self):
        """
        """
        pass
