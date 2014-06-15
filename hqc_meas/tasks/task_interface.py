# -*- coding: utf-8 -*-
#==============================================================================
# module : task_interface.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from atom.api import Atom, ForwardInstance, Instance, Str

from hqc_meas.utils.atom_util import HasPrefAtom
from hqc_meas.tasks.base_tasks import SimpleTask, BaseTask
from ..utils.atom_util import member_from_str, tagged_members


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

    def perform(self, *args, **kwargs):
        """

        """
        return self.interface.perform(*args, **kwargs)

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
        #XXXX Here I will assume that answer is the one from the BaseTask
        # and assume the interface does not override any task member.
        # For the callables only the not None answer will be updated.
        answers = BaseTask.answer(self, members, callables)
        interface_answers = self.interface.answer(members, callables)
        answers.update(interface_answers)
        return answers

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

        if self.interface:
            prefs = self.interface.preferences_from_members()
            self.task_preferences['interface'] = prefs

    update_preferences_from_members = register_preferences

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
        task = cls()
        for name, member in tagged_members(task, 'pref').iteritems():

            if name not in config:
                continue

            value = config[name]
            converted = member_from_str(member, value)
            setattr(task, name, converted)

        if 'interface' in config:
            inter_class_name = config['interface'].pop('interface_class')
            inter_class = dependencies['interfaces'][inter_class_name]
            task.interface = inter_class.build_from_config(config['interface'],
                                                           dependencies)

    def _observe_interface(self, change):
        """ Observer.

        """
        if 'oldvalue' in change and change['oldvalue']:
            change['oldvalue'].task = None
        if change['value']:
            change['value'].task = self


class TaskInterface(HasPrefAtom):
    """
    """
    #: Flag indicating to the manager whether to expect a view or not.
    #: Class attribute
    has_view = False

    #: A reference to which this interface is linked.
    task = Instance(SimpleTask)

    #: Name of the class of the interface. Used for persistence purposes.
    interface_class = Str().tag(pref=True)

    def check(self, *args, **kwargs):
        """

        This is the reponsability of the task to call this method.

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
