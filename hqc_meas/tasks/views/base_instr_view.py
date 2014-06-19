# -*- coding: utf-8 -*-
#==============================================================================
# module : base_intr_view.enaml
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
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

    padding = set_default((0, 0, 5, 5))

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
            drivers = []
            interfaces = {}
            for i in inter[self.task.task_class]:
                drivers.extend(i.driver_list)
                interfaces.update({d: i for d in i.driver_list})
            self.drivers = drivers
            self._interfaces = interfaces
        else:
            self.drivers = self.task.driver_list

        self._update_profiles({})
        self._bind_observers()

    def destroy(self):
        """ Overriden destroyer to remove observers from instr manager state.

        """
        self._unbind_observers()
        super(BaseInstrumentView, self).destroy()

    #--- Private API ----------------------------------------------------------

    #: Map between driver and interface.
    _interfaces = Dict(Str())

    def _update_interface(self, change):
        """ Update the interface when the selected driver change.

        """
        driver = self.task.selected_driver
        interface = self._interfaces[driver]
        if type(self.task.interface) != interface:
            self.task.interface = interface()
            cmd = 'hqc_meas.task_manager.interface_views_request'
            views, _ = self.core.invoke_command(cmd,
                                                {'interface_classes':
                                                    [interface.__name__]}
                                                )
            for i_v in self.i_views:
                i_v.destroy()

            if interface.has_view:
                i_views = [v(self, interface=self.task.interface)
                           for v in views[interface.__name__]]
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
        """ Undind the observers at widget destruction.

        """
        self.instr_man_state.unobserve('all_profiles', self._update_profiles)
        self.task.unobserve('selected_driver', self._update_profiles)
        if isinstance(self.task, InterfaceableTaskMixin):
            self.task.unobserve('selected_driver', self._update_interface)
