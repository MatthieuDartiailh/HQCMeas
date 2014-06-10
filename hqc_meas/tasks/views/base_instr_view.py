# -*- coding: utf-8 -*-
from atom.api import Typed, Value, Instance, List, Str, set_default
from enaml.widgets.api import GroupBox
from enaml.workbench.core.core_plugin import CorePlugin
from enaml.core.declarative import d_

from hqc_meas.tasks.api import InstrumentTask

# XXXX add handling interfaces according to driver.


class BaseInstrumentView(GroupBox):
    """ Base class for instrument task views.

    This class handles internally the access to the profiles.

    """
    #: Reference to the task being edited by this view.
    task = d_(Instance(InstrumentTask))

    #: List of profiles matching the currently selected one.
    profiles = d_(List(Str()))

    #: Reference to the core plugin of the application.
    core = d_(Typed(CorePlugin))

    #: Reference to the InstrManager State.
    instr_man_state = Value()

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
        self._update_profiles({})
        self._bind_observers()

    def destroy(self):
        """ Overriden destroyer to remove observers from instr manager state.

        """
        self._unbind_observers()
        super(BaseInstrumentView, self).destroy()

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

    def _unbind_observers(self):
        """ Undind the observers at widget destruction.

        """
        self.instr_man_state.unobserve('all_profiles', self._update_profiles)
        self.task.unobserve('selected_driver', self._update_profiles)
