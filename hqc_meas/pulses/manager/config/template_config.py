# -*- coding: utf-8 -*-
# =============================================================================
# module : pulses/manager/config/template_config.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""

"""
from atom.api import (Str, Value, Bool, Typed, observe)
from copy import deepcopy
from ast import literal_eval

from .base_config import AbstractConfig
from ..sequences.template_sequence import TemplateSequence
from ..contexts.template_context import TemplateContext
from ..base_sequences import Sequence
from ..pulse import Pulse


# Circular import protection
def pulses_manager():
    from ..plugin import PulsesManagerPlugin
    return PulsesManagerPlugin


class TemplateConfig(AbstractConfig):
    """ Config used to insert a template into a sequence.

    The template can either be inserted as a TemplateSequence or merged.
    In the first case it will appear as a single item and the only inputs will
    be the declared template vars and the mapping between the true context of
    execution channels and the ones from the template context. The id of the
    template will be kept and the template will be re-used each time the
    sequence is rebuilt.
    In the second the template will be unraveled and inserted as many items,
    the user will be allowed to choose where the template vars should appear
    and to give a mapping between the contexts channels.

    """
    #: Name of the sequence used to make the sequence easier to read.
    template_name = Str()

    #: Docstring of the sequence.
    template_doc = Str()

    #: Configobj object descrtibing the template.
    template_config = Value()

    #: Flag indicating whether the Template should be merged as a standard
    #: sequence or included as a TemplateSequence. In the first case all
    #: reference to the template is lost, in the second the template sequence
    #: rememeber its templates and use it when rebuilding itself.
    merge = Bool(True)

    #: When merging should the template vars be added as local_vars or
    #: external_vars in the root.
    t_vars_as_root = Bool()

    #: False template context used to determine the mapping between the
    #: template context channels and the ones from the root.
    #:  Only used in merge mode.
    context = Typed(TemplateContext)

    def build_sequence(self):
        """ Build sequence using the selected template.

        """
        core = self.manager.workbench.get_plugin('enaml.workbench.core')
        cmd = 'hqc_meas.dependencies.collect'
        res, dep = core.invoke_command(cmd, {'obj': self.template_config})
        if not res:
            self.errors = dep
            return

        config = self.template_config
        config['name'] = self.template_name

        if not self.merge:
            seq = TemplateSequence.build_from_config(config, dep)
            return seq

        else:
            t_vars = literal_eval(config.pop('template_vars'))
            if not self.t_vars_as_root:
                loc_vars = literal_eval(config['local_vars'])
                loc_vars.update(t_vars)
                config['local_vars'] = repr(loc_vars)
            else:
                self.root.update(t_vars)

            _, t_config, _ = dep['pulses']['templates'][config['template_id']]
            # Don't want to alter the dependencies dict in case somebody else
            # use the same template.
            t_config = deepcopy(t_config)
            t_config.merge(config)
            config = t_config

            seq = Sequence.build_from_config(t_config, dep)

            self._apply_mapping(seq)

            return seq

    @observe('template_name')
    def check_parameters(self, change):
        """ Observer notifying that the configurer is ready to build.

        """
        if change['value']:
            self.config_ready = True
        else:
            self.config_ready = False

    # --- Private API ---------------------------------------------------------

    def _apply_mapping(self, seq):
        """ Apply the user defined mapping of channels for the pulses.

        """
        c_mapping = self.context.channel_mapping
        for item in seq.items:
            if isinstance(item, Pulse):
                item.channel = c_mapping.get(item.channel, '')
            elif isinstance(item, TemplateSequence):
                mapping = item.context.channel_mapping
                for channel in mapping:
                    mapping[channel] = c_mapping.get(item.channel, '')
            elif isinstance(item, Sequence):
                self._apply_mapping(item)

    def _default_context(self):
        """ Initialize tthe context using the config.

        """
        config = self.template_config
        context = TemplateContext()
        context.update_members_from_preferences(config['context'])
        return context
