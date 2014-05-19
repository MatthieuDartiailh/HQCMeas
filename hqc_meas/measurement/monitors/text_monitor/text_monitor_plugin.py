# -*- coding: utf-8 -*-
#==============================================================================
# module : text_monitor_plugin.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
import logging
from atom.api import Str, List, Subclass, Dict

from hqc_meas.utils.has_pref_plugin import HasPrefPlugin
from ..base_monitor import Monitor
from .rules import AbstractMonitorRule, TEXT_MONITOR_RULES
from .monitor import TextMonitor


class TextMonitorPlugin(HasPrefPlugin):
    """
    """

    #--- Public API -----------------------------------------------------------

    # List of rules which should be created automatically for new monitors.
    default_rules = List(Str()).tag(pref=True)

    # Mapping between rules class names and rule classes.
    rules_classes = Dict(Str(), Subclass(AbstractMonitorRule))

    # Dict holding the infos necessary to rebuild rules on demand.
    rules = Dict(Str(), Dict()).tag(pref=True)

    def build_rule(self, rule_config):
        """ Build rule from a dict.

        Parameters
        ----------
        rule_config : dict
            Dict containing the infos to build the rule from scratch.

        Returns
        -------
        rule : AbstractMonitorRule
            New rule properly initialized.

        """
        class_name = rule_config.pop('class')
        rule_class = self.rules_classes.get(class_name)
        if rule_class is not None:
            rule = rule_class()
            rule.update_members_from_preferences(**rule_config)

            return rule

        else:
            logger = logging.getLogger(__name__)
            mess = 'Requested rule class not found : {}'.format(class_name)
            logger.warn(mess)

    def create_monitor(self, raw=False):
        """ Create a new monitor.

        Parameters
        ----------
        raw : bool, optionnal
            Whether or not to add the default rules to the new monitor.

        Returns
        -------
        monitor : TextMonitor
            New text monitor.

        """
        exts = [e for e in self.manifest.extensions if e.id == 'monitors']
        decl = exts[0].get_child(Monitor)
        monitor = TextMonitor(_plugin=self,
                              declaration=decl)

        if not raw:
            rules = []
            for rule_name in self.default_rules:
                config = self.rules.get(rule_name)
                if config is not None:
                    rule = self.build_rule(config)
                    rules.append(rule)
                else:
                    logger = logging.getLogger(__name__)
                    mess = 'Requested rule not found : {}'.format(rule_name)
                    logger.warn(mess)

            monitor.rules = rules

        return monitor

    #--- Private API ----------------------------------------------------------

    def _default_rules_classes(self):
        """ Default builder for the rules_classes.

        """
        return {rule.__name__: rule for rule in TEXT_MONITOR_RULES}
