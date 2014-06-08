# -*- coding: utf-8 -*-
#==============================================================================
# module : task_interface.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from atom.api import Atom, ForwardInstance, Instance

from hqc_meas.atom_util import HasPrefAtom
from hqc_meas.tasks.base_tasks import SimpleTask
from ..utils.atom_util import member_from_str, tagged_members


class InterfaceableTaskMixin(Atom):
    """ Mixin class for defining simple task using interfaces.

    """
    #: A reference to the current interface for the task.
    interface = ForwardInstance(lambda: TaskInterface)

    def check(self, **kwargs):
        """

        """
        return self.interface.check(**kwargs)

    def perform(self, *args, **kwargs):
        """

        """
        return self.interface.perform(*args, **kwargs)

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

        prefs = self.interface.preferences_from_members()
        self.task_preferences['interface'] = prefs

    update_preferences_from_members = register_preferences

    def update_members_from_preferences(self, parameters):
        """ Update the members values using a dict.

        Parameters
        ----------
        parameters : dict(str: str)
            Dictionary holding the new values to give to the members in string
            format, save for the interface which is assumed to have been
            reconstructed.

        """
        for name, member in tagged_members(self, 'pref').iteritems():

            if name not in parameters:
                continue

            old_val = getattr(self, name)
            if isinstance(old_val, HasPrefAtom):
                old_val.update_members_from_preferences(**parameters[name])

            value = parameters[name]
            converted = member_from_str(member, value)
            setattr(self, name, converted)

        if 'interface' in parameters:
            self.interface = parameters['interface']

    def _observe_interface(self, change):
        """ Observer.

        """
        if 'oldvalue' in change:
            change['oldvalue'].task = None

        change['value'].task = self


class TaskInterface(HasPrefAtom):
    """
    """
    #: A reference to which this interface is linked.
    task = Instance(SimpleTask)
