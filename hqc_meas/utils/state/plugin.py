# -*- coding: utf-8 -*-
# =============================================================================
# module : utils/state/plugin.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
import contextlib
from atom.api import (Atom, Unicode, Dict, Bool, Tuple, Typed, Value,
                      Property)
from enaml.workbench.api import Plugin, Extension
from new import classobj
from .state import State


class _StateHolder(Atom):
    """ Base class for all state holders of the state plugin.

    This base class is subclassed at runtime to create custom Atom object with
    the right members.

    """
    alive = Bool(True)

    _allow_set = Bool(False)

    def __setattr__(self, name, value):
        if self._allow_set or name == '_allow_set':
            super(_StateHolder, self).__setattr__(name, value)
        else:
            raise AttributeError('Attributes of states holder are read-only')

    @contextlib.contextmanager
    def setting_allowed(self):
        """ Context manager to prevent users of the state to corrupt it

        """
        self._allow_set = True
        try:
            yield
        finally:
            self._allow_set = False

    def updater(self, changes):
        """ Observer handler keeping the state up to date with the plugin.

        """
        with self.setting_allowed():
            setattr(self, changes['name'], changes['value'])


STATES_POINT = u'hqc_meas.state.states'


class StatePlugin(Plugin):
    """ A plugin to manage application wide available states

    """

    def start(self):
        """ Start the plugin life-cycle.

        This method is called by the framework at the appropriate time. It
        should never be called by user code.

        """
        self._states = {}
        self._refresh_states()
        self._bind_observers()

    def stop(self):
        """ Stop the plugin life-cycle.

        This method is called by the framework at the appropriate time.
        It should never be called by user code.

        """
        self._unbind_observers()
        self._states.clear()

    def get_state(self, state_id):
        """ Return the state associated to the state id

        """
        pl_id, decl, cl, state = self._states[unicode(state_id)]
        if not state:
            state = self._create_state_object(pl_id, decl, cl)
            self._states[unicode(state_id)] = (pl_id, decl, cl, state)

        return state

    # --- Private API ---------------------------------------------------------

    #: Dict storing the plugin_id, the state decl, the runtime class and the
    #: instance if it has been created.
    _states = Dict(Unicode(), Tuple())

    _state_extensions = Dict(Typed(Extension), Tuple())

    def _refresh_states(self):
        """ Refresh the list of states contributed by extensions.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(STATES_POINT)
        extensions = point.extensions

        # If no extension remains clear everything
        if not extensions:
            self._notify_state_death(self._state_extensions.keys())
            self._states.clear()
            self._state_extensions.clear()
            return

        # Notify the death of the state whose extensions have been removed
        dead_extensions = [extension for extension in self._state_extensions
                           if extension not in extensions]
        self._notify_state_death(dead_extensions)

        # Keep track of which extension declared which state (keep triplet :
        # declaration, run-time class, state object)
        new_extensions = dict()
        old_extensions = self._state_extensions
        for extension in extensions:
            if extension in old_extensions:
                state = old_extensions[extension]
            else:
                state = self._load_state(extension)

            new_extensions[extension] = state

        # Build the mapping between state ids and states object
        states = {}
        for extension in extensions:
            state = new_extensions[extension]
            state_decl = state[1]
            if state_decl.id in states:
                msg = "state '%s' is already registered"
                raise ValueError(msg % state_decl.id)
            if not state_decl.sync_members and not state_decl.prop_getters:
                msg = "state '%s' does not declare any attribute"
                raise ValueError(msg % state_decl.id)
            states[state_decl.id] = tuple(list(state)+[None])

        self._states = states
        self._state_extensions = new_extensions

    def _load_state(self, extension):
        """ Create a custom _StateHolder class at runtime.

        Parameters
        ----------
        extension : Extension
            Extension contributing to the state extension point for which a
            custom _StateHolder class should be build

        Returns
        -------
        state_tuple: tuple
            Tuple containing the State declaration used to build the state
            holder and  the custom class derived _StateHolder dynamically
            created.

        """
        # Getting the state declaration contributed by the extension, either
        # as a child or returned by the factory. Only the first state is
        # considered.
        # TODO add support for arbitrary number of state per extension
        # TODO add support for dotted_names as sync_member
        workbench = self.workbench
        states = extension.get_children(State)
        if extension.factory is not None and not states:
            state = extension.factory(workbench)
            if not isinstance(state, State):
                msg = "extension '%s' created non-State of type '%s'"
                args = (extension.qualified_id, type(state).__name__)
                raise TypeError(msg % args)
        else:
            state = states[0]

        # Dynamic building of the state class
        # TODO add check sync_members and prop not confincting
        class_name = str(state.id.replace('.', '').capitalize())

        members = {}
        for m in state.sync_members:
            members[m] = Value()
        for p in state.prop_getters:
            members[p] = Property()
        state_class = classobj(class_name, (_StateHolder,), members)

        return (extension.plugin_id, state, state_class)

    def _create_state_object(self, plugin_id, state, state_class):
        """ Instantiate state object.

        """
        # Instantiation , initialisation, and binding of the state object to
        # the plugin declaring it.
        state_object = state_class()
        plugin = self.workbench.get_plugin(plugin_id)
        for m in state.sync_members:
            with state_object.setting_allowed():
                setattr(state_object, m, getattr(plugin, m))
            plugin.observe(m, state_object.updater)
        for p in state.prop_getters:
            prop = state_object.get_member(p)
            prop.getter(getattr(plugin, state.prop_getters[p]))

        return state_object

    def _notify_state_death(self, dead_extensions):
        """ Notify that the plugin contributing a state is not plugged anymore.

        """
        states = self._state_extensions
        for dead_state in dead_extensions:
            state_id = states[dead_state][1].id
            _, _, _, state = self._states[state_id]
            if state:
                with state.setting_allowed():
                    state.alive = False

    def _on_states_updated(self, change):
        """ The observer for the state extension point

        """
        self._refresh_states()

    def _bind_observers(self):
        """ Setup the observers for the plugin.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(STATES_POINT)
        point.observe('extensions', self._on_states_updated)

    def _unbind_observers(self):
        """ Remove the observers for the plugin.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(STATES_POINT)
        point.unobserve('extensions', self._on_states_updated)

        #TODO also unbind dynamic observers here in case there is any remaining
