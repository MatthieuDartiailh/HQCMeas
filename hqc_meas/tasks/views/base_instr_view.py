# -*- coding: utf-8 -*-
# =============================================================================
# module : base_intr_view.enaml
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import (Typed, Value, Instance, List, Str, set_default, Dict,
                      Tuple)
from enaml.widgets.api import GroupBox
from enaml.workbench.core.core_plugin import CorePlugin
from enaml.core.declarative import d_

from hqc_meas.tasks.api import InstrumentTask, InterfaceableTaskMixin


class BaseInstrumentView(GroupBox):
    """ Base class for instrument task views.

    This class handles internally the access to the profiles.

    """
    #: Reference to the task being edited by this view.
    task = d_(Instance(InstrumentTask))

    #: List of drivers which can be used with that task.
    drivers = d_(List(Str()))

    #: List of profiles matching the currently selected one.
    profiles = d_(List(Str()))

    #: Reference to the core plugin of the application.
    core = d_(Typed(CorePlugin))

    #: Reference to the InstrManager State.
    instr_man_state = Value()

    #: References to the currently instantiated interface views.
    i_views = Tuple(default=())

    padding = set_default((0, 2, 2, 2))

    def initialize(self):
        """ Overrridden initializer to get a ref to the instr manager state on
        start up.

        """
        super(BaseInstrumentView, self).initialize()
        cmd = 'hqc_meas.state.get'
        state = self.core.invoke_command(cmd,
                                         {'state_id':
                                          'hqc_meas.states.instr_manager'})
        self.instr_man_state = state
        if isinstance(self.task, InterfaceableTaskMixin):
            cmd = 'hqc_meas.task_manager.interfaces_request'
            inter, _ = self.core.invoke_command(cmd,
                                                {'tasks':
                                                    [self.task.task_class]}
                                                )
            # Get the drivers defined on the tasks ie using the default
            # interface implemented through i_perform
            drivers = self.task.driver_list[:]
            interfaces = {driver: type(None) for driver in drivers}

            # Map driver to their interface.
            for i in inter.get(self.task.task_class, []):
                drivers.extend(i.driver_list)
                interfaces.update({d: i for d in i.driver_list})
            self.drivers = drivers
            self._interfaces = interfaces
        else:
            self.drivers = self.task.driver_list

        if getattr(self.task, 'interface', None):
            self._insert_interface_views(self.task.interface)

        self._update_profiles({})
        self._bind_observers()

    def destroy(self):
        """ Overriden destroyer to remove observers from instr manager state.

        """
        self._unbind_observers()
        super(BaseInstrumentView, self).destroy()

    # --- Private API ---------------------------------------------------------

    #: Map between driver and interface.
    _interfaces = Dict(Str())

    def _update_interface(self, change):
        """ Update the interface when the selected driver change.

        """
        driver = self.task.selected_driver
        interface = self._interfaces[driver]

        # The or clause handle the absence of an interface (ie None for both
        # interface and task.interface).
        if type(self.task.interface) != interface:
            # Destroy the views associated with the ancient interface.
            for i_v in self.i_views:
                i_v.destroy()

            # If no interface is used simply assign None
            if type(None) == interface:
                self.task.interface = None
                return

            # Otherwise create interface and insert its views.
            self.task.interface = interface()

            self._insert_interface_views(self.task.interface)

    def _insert_interface_views(self, interface):
        """ Insert trhe view associated with an interface instance.

        """
        cmd = 'hqc_meas.task_manager.interface_views_request'
        i_c_name = type(interface).__name__
        views, _ = self.core.invoke_command(cmd,
                                            {'interface_classes': [i_c_name]}
                                            )

        if interface.has_view:
            i_views = [v(self, interface=self.task.interface)
                       for v in views[i_c_name]]
            # TODO handle more complex insertions.
            if hasattr(i_views[0], 'index'):
                self.insert_children(i_views[0].index, i_views)
            else:
                self.insert_children(None, i_views)

            self.i_views = tuple(i_views)

        else:
            self.i_views = ()

    def _update_profiles(self, change):
        """ Update the list of matching profiles for the selected driver.

        """
        driver = self.task.selected_driver
        if driver:
            cmd = 'hqc_meas.instr_manager.matching_profiles'
            self.profiles = self.core.invoke_command(cmd,
                                                     {'drivers': [driver]})

    def _bind_observers(self):
        """ Bind the observers at widget initialisation.

        """
        self.instr_man_state.observe('all_profiles', self._update_profiles)
        self.task.observe('selected_driver', self._update_profiles)
        if isinstance(self.task, InterfaceableTaskMixin):
            self.task.observe('selected_driver', self._update_interface)

    def _unbind_observers(self):
        """ Unbind the observers at widget destruction.

        """
        self.instr_man_state.unobserve('all_profiles', self._update_profiles)
        self.task.unobserve('selected_driver', self._update_profiles)
        if isinstance(self.task, InterfaceableTaskMixin):
            self.task.unobserve('selected_driver', self._update_interface)
