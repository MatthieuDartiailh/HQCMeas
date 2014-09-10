# -*- coding: utf-8 -*-
# =============================================================================
# module : pulses.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from atom.api import (Dict, ForwardTyped, Unicode)
from inspect import cleandoc

from ..entry_eval import eval_entry
from ..base_sequences import BaseSequence, Sequence


def context():
    from ..contexts.template_context import TemplateContext
    return TemplateContext


class TemplateSequence(BaseSequence):
    """ Sequence used to represent a template in a Sequence.

    """
    # --- Public API ----------------------------------------------------------

    #: Id of the template on which this sequence relies.
    template_id = Unicode().tag(pref=True)

    #: Dict of variables defined in the template scope.
    template_vars = Dict().tag(pref=True)

    #: Documentation of the template as provided by the user.
    docs = Unicode()

    #: Special context providing channel mapping.
    context = ForwardTyped(context)

    def compile_sequence(self, root_vars, sequence_locals, missings, errors):
        """

        """
        # Check the channel mapping makes sense.
        if not self.context.prepare_compilation(self, errors):
            return False, []

        # Definition evaluation.
        self.eval_entries(root_vars, sequence_locals, missings, errors)

        prefix = '{}_'.format(self.index)
        # Template vars evaluation.
        for name, formula in self.template_vars.iteritems():
            if name not in self._evaluated_vars:
                try:
                    val = eval_entry(formula, sequence_locals, missings)
                    self._evaluated_vars[name] = val
                except Exception as e:
                    errors[prefix + name] = repr(e)

        # Local vars computation.
        for name, formula in self.local_vars.iteritems():
            if name not in self._evaluated_vars:
                try:
                    val = eval_entry(formula, sequence_locals, missings)
                    self._evaluated_vars[name] = val
                except Exception as e:
                    errors[prefix + name] = repr(e)

        local_namespace = self._evaluated_vars.copy()
        local_namespace['sequence_end'] = self.duration

        res, pulses = self._compile_items(local_namespace, local_namespace,
                                          missings, errors)

        if res:
            t_start = self.start
            c_mapping = self.context.channel_mapping
            for pulse in pulses:
                pulse.start += t_start
                pulse.stop += t_start
                pulse.channel = c_mapping[pulse.channel]

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

    def preferences_from_members(self):
        """ Get the members values as string to store them in .ini files.

        Reimplemented here to save context.

        """
        pref = super(TemplateSequence, self).preferences_from_members()

        pref['context'] = self.context.preferences_from_members()

        return pref

    def update_members_from_preferences(self, **parameters):
        """ Use the string values given in the parameters to update the members

        This function will call itself on any tagged HasPrefAtom member.
        Reimplemented here to update context.

        """
        super(TemplateSequence,
              self).update_members_from_preferences(**parameters)

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
        sequence : TemplateSequence
            Newly created and initiliazed sequence.

        """
        # First get the underlying template from the dependencies and merge
        # config into it as it has more recent infos about the context and
        # the vars.
        dep = dependencies['pulses']
        _, t_config, doc = dep['templates'][config['template_id']]
        t_config.merge(config)
        config = t_config

        context_config = config['context']
        context_class_name = context_config.pop('context_class')
        context_class = dep['contexts'][context_class_name]
        context = context_class()
        context.update_members_from_preferences(**context_config)

        seq = super(TemplateSequence, cls).build_from_config(t_config,
                                                             dependencies)
        seq.docs = doc
        seq.context = context

        # Do the indexing of the children once and for all.
        i = 1
        for item in seq.items:
            item.index = i
            item.root = seq
            if isinstance(item, Sequence):
                item._recompute_indexes()
                i = item._last_index + 1
            else:
                i += 1

        return seq

    # --- Private API ---------------------------------------------------------

    def _observe_context(self, change):
        """ Make sure the context has a ref to the sequence.

        """
        c = change['value']
        if c:
            c.template = self
