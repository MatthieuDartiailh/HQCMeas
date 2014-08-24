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
    context = Typed(BaseContext)

    def compile_sequence(self, sequence_locals, missing_locals, errors):
        """

        """
        pass

    def get_bindable_vars(self):
        """ Access the list of bindable vars for the sequence.

        """
        return self.linkable_vars + self.template_vars.keys()

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
        super(TemplateSequence,
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
        return super(TemplateSequence, cls).build_from_config(config,
                                                              dependencies)
