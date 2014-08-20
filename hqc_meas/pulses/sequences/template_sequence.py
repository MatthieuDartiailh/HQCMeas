# -*- coding: utf-8 -*-
# =============================================================================
# module : pulses.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from atom.api import (Dict, Typed)

from .contexts.base_context import BaseContext
from .entry_eval import eval_entry
from ..pulses import Sequence


class TemplateSequence(Sequence):
    """

    """
    # --- Public API ----------------------------------------------------------

    #: Dict of variables defined in the template scope.
    template_vars = Dict().tag(pref=True)

    #: Dict mapping local channel to the true context channel.
    channel_mapping = Dict().tag(pref=True)

    #: Special context providing channel mapping.
    t_context = Typed(BaseContext)

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
                - a context dependent result.

        """
        missings = set()
        errors = {}
        sequence_locals = self.external_vars.copy()

        if self.fix_sequence_duration:
            try:
                duration = eval_entry(self.sequence_duration, sequence_locals,
                                      missings)
                sequence_locals['sequence_end'] = duration
            except Exception as e:
                errors['root_seq_duration'] = repr(e)

        res, pulses = super(TemplateSequence,
                            self).compile_sequence(sequence_locals,
                                                   missings, errors)

        if not res:
            return False, (missings, errors)

        elif not use_context:
            return True, pulses

        else:
            kwargs = {}
            if self.fix_sequence_duration:
                kwargs['sequence_duration'] = duration
            return self.context.compile_sequence(pulses, **kwargs)

    def get_bindable_vars(self):
        """ Access the list of bindable vars for the sequence.

        """
        return self.linkable_vars + self.external_vars.keys()

    def preferences_from_members(self):
        """ Get the members values as string to store them in .ini files.

        Reimplemented here to save context.

        """
        pref = super(TemplateSequence, self).preferences_from_members()

        pref['t_context'] = self.context.preferences_from_members()

        return pref

    def update_members_from_preferences(self, **parameters):
        """ Use the string values given in the parameters to update the members

        This function will call itself on any tagged HasPrefAtom member.
        Reimplemented here to update context.

        """
        super(TemplateContext,
              self).update_members_from_preferences(**parameters)

        para = parameters['t_context']
        self.t_context.update_members_from_preferences(**para)

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
        context_class = dependencies['pulses'][context_class_name]
        context = context_class()
        context.update_members_from_preferences(**context_config)
        config['context'] = context
        return super(RootSequence, cls).build_from_config(config,
                                                          dependencies)
