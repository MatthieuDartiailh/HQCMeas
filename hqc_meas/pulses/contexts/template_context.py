# -*- coding: utf-8 -*-
# =============================================================================
# module : template_context.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""

"""
from atom.api import Float, List, Dict, Typed
from .base_context import BaseContext
from ..sequences.template_sequence import TemplateSequence


class TemplateContext(BaseContext):
    """
    """
    #: Declared analogical channels to use inside the template.
    analogical_channels = List().tag(pref=True)

    #: Declared logical channels to use inside the template.
    logical_channels = List().tag(pref=True)

    #: Mapping between the template channels and the channels of the true
    #: context.
    channel_mapping = Dict().tag(pref=True)

    #: Reference to the template sequence to which this context is attached.
    template = Typed(TemplateSequence)

    def prepare_compilation(self, errors):
        """

        """
        context = self.template.root.context
        self._sampling_time = context.sampling_time
        self.time_unit = context.time_unit
        self.rectify_time = context.rectify_time
        self.tolerance = context.tolerance
        mess = 'Missing/Erroneous mapping for channels {}'
        mapping = self.channel_mapping
        c_errors = [c for c in self.analogical_channels
                    if c not in mapping
                    or mapping[c] not in context.analogical_channels]
        c_errors.extend([c for c in self.logical_channels
                         if c not in mapping
                         or mapping[c] not in context.logical_channels])
        if c_errors:
            errors['{}-context'.format(self.template.name)] = \
                mess.format(c_errors)
            return False

        return True

    # --- Private API ---------------------------------------------------------

    _sampling_time = Float()

    def _get_sampling_time(self):
        """ Getter for the sampling time prop of BaseContext.

        """
        return self._sampling_time


CONTEXTS = {'Template': TemplateContext}
