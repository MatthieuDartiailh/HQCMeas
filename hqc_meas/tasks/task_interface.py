# -*- coding: utf-8 -*-
# =============================================================================
# module : task_interface.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import Atom, ForwardInstance, Instance, Str, Dict
from inspect import cleandoc

from hqc_meas.utils.atom_util import HasPrefAtom
from hqc_meas.tasks.base_tasks import BaseTask


class InterfaceableTaskMixin(Atom):
    """ Mixin class for defining simple task using interfaces.

    When defining a new interfaceablke task this mixin should always be the
    letf most class when defining the inheritance. This is due to the Python
    Method Resolution Order (mro) and the fact that this mixin must override
    methods defined in tasks.
    ex : Toto(InterfaceableTaskMixin, MyTask):


    """
    #: A reference to the current interface for the task.
    interface = ForwardInstance(lambda: TaskInterface)

    def check(self, *args, **kwargs):
        """ Check the interface.

        This run the checks of the next parent class in the mro and check
        if a valid interface (real or default one) exists.

        """
        # Trick to call parent check by tweaking the mro.
        # XXXX won't work if InterfaceableTaskMixin appears several times in
        # the mro
        ancestors = type(self).mro()
        if ancestors.count(InterfaceableTaskMixin) > 1:
            return False, {self.task_name: cleandoc('''Task cannot inherit
                multiple times from InterfaceableTaskMixin''')}
        i = ancestors.index(InterfaceableTaskMixin)
        test, traceback = ancestors[i + 1].check(self, *args, **kwargs)

        if not self.interface and not hasattr(self, 'i_perform'):
            traceback[self.task_name + '_interface'] = 'Missing interface'
            return False, traceback

        if self.interface:
            i_test, i_traceback = self.interface.check(*args, **kwargs)

            traceback.update(i_traceback)
            test &= i_test

        return test, traceback

    def perform(self, *args, **kwargs):
        """ Implementation of perform relying on interfaces.

        This method will be considered as the true perform method of the task,
        it will either call the interface perform method or the special
        i_perform method if there is no interface. This is meant to provide
        an easy way to turn a non-interfaced task into an interfaced one :
        - add the mixin as the left most inherited class
        - rename the perform method to i_perform
        - create new interfaces but keep the default 'standard' behaviour.

        NEVER OVERRIDE IT IN SUBCLASSES OTHERWISE YOU WILL BREAK THE
        INTERFACE SYSTEM.

        """
        if self.interface:
            return self.interface.perform(*args, **kwargs)
        else:
            return self.i_perform(*args, **kwargs)

    def answer(self, members, callables):
        """ Method used by to retrieve information about a task.

        Reimplemented here to also explore the interface.

        Parameters
        ----------
        members : list(str)
            List of members names whose values should be returned.

        callables : dict(str, callable)
            Dict of name callable to invoke on the task or interface to get
            some infos.

        Returns
        -------
        infos : dict
            Dict holding all the answers for the specified members and
            callables.

        """
        # I assume the interface does not override any task member.
        # For the callables only the not None answer will be updated.

        ancestors = type(self).mro()
        # XXXX here no check that the mixin apperas only once.
        i = ancestors.index(InterfaceableTaskMixin)
        answers = ancestors[i + 1].answer(self, members, callables)

        interface_answers = self.interface.answer(members, callables)
        answers.update(interface_answers)
        return answers

    def register_preferences(self):
        """ Register the task preferences into the preferences system.

        """
        ancestors = type(self).mro()
        # XXXX here no check that the mixin apperas only once.
        i = ancestors.index(InterfaceableTaskMixin)
        ancestors[i + 1].register_preferences(self)

        if self.interface:
            prefs = self.interface.preferences_from_members()
            self.task_preferences['interface'] = prefs

    def update_preferences_from_members(self):
        """ Update the values stored in the preference system.

        """
        ancestors = type(self).mro()
        # XXXX here no check that the mixin apperas only once.
        i = ancestors.index(InterfaceableTaskMixin)
        ancestors[i + 1].update_preferences_from_members(self)

        if self.interface:
            prefs = self.interface.preferences_from_members()
            self.task_preferences['interface'] = prefs

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
            This is assembled by the TaskManager.

        Returns
        -------
        task :
            Newly built task.

        """
        ancestors = cls.mro()
        # XXXX here no check that the mixin apperas only once.
        i = ancestors.index(InterfaceableTaskMixin)
        task = ancestors[i + 1].build_from_config(cls)

        if 'interface' in config:
            inter_class_name = config['interface'].pop('interface_class')
            inter_class = dependencies['interfaces'][inter_class_name]
            task.interface = inter_class.build_from_config(config['interface'],
                                                           dependencies)

    def _observe_interface(self, change):
        """ Observer ensuring the interface always has a valid ref to the task
        and that the interface database entries are added to the task one.

        """
        # XXXX Workaround Atom _DictProxy issue.
        new_entries = dict(self.task_database_entries)
        if 'oldvalue' in change and change['oldvalue']:
            inter = change['oldvalue']
            inter.task = None
            for entry in inter.interface_database_entries:
                new_entries.pop(entry, None)

        if change['value']:
            inter = change['value']
            inter.task = self
            for entry, value in inter.interface_database_entries.iteritems():
                new_entries[entry] = value

        self.task_database_entries = new_entries


class TaskInterface(HasPrefAtom):
    """
    """
    #: Flag indicating to the manager whether to expect a view or not.
    #: Class attribute
    has_view = False

    #: A reference to which this interface is linked.
    task = Instance(BaseTask)

    #: Name of the class of the interface. Used for persistence purposes.
    interface_class = Str().tag(pref=True)

    #: Dict of database entries added by the interface.
    interface_database_entries = Dict(Str())

    def check(self, *args, **kwargs):
        """

        """
        return True, {}

    def perform(self, *args, **kwargs):
        """

        """
        raise NotImplementedError()

    def answer(self, members, callables):
        """ Method used by to retrieve information about a task.

        Parameters
        ----------
        members : list(str)
            List of members names whose values should be returned.

        callables : dict(str, callable)
            Dict of name callable to invoke on the task or interface to get
            some infos.

        Returns
        -------
        infos : dict
            Dict holding all the answers for the specified members and
            callables. Contrary to what happens for task this one will never
            contain None as a value.

        """
        answers = {m: getattr(self, m, None) for m in members}
        answers.update({k: c(self) for k, c in callables.iteritems()})
        for key, val in answers.copy().iteritems():
            if val is None:
                del answers[key]

        return answers

    @classmethod
    def build_from_config(cls, config, dependencies):
        """ Create an interface using the provided dict.

        """
        interface = cls()
        interface.update_members_from_preferences(**config)
        return interface

    def _default_interface_class(self):
        """ Default value for the class_name member.

        """
        return type(self).__name__
