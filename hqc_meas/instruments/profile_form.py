# -*- coding: utf-8 -*-
#==============================================================================
# module : profile_form.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""

from atom.api import (Atom, List, Str, Unicode, Instance, Typed)

from .forms import AbstractConnectionForm, FORMS
from .manager_plugin import InstrManagerPlugin


class ProfileForm(Atom):
    """
    Simple model representing the informations stored in an instrument profile.

    Parameters
    ----------
    **kwargs
        Keyword arguments used to initialize attributes and form attributes

    Attributes
    ----------
    manager: InstrManagerPlugin
        A reference to the current instrument manager.
    name : str
        Name of the instrument used to identify him. Should be different from
        the driver name
    driver_type : str
        Kind of driver to use, ie which kind of standard is used to
        communicate
    driver_list : list(Unicodestr)
        List of known driver matching `driver_type`
    driver : str
        Name of the selected driver
    connection_form : instance(AbstractConnectionForm)
        Form used to display the informations specific to the `driver_type`


    """
    manager = Typed(InstrManagerPlugin)
    name = Unicode('')
    driver_type = Str('')
    drivers = List(Str(), [])
    driver = Str('')
    connection_form = Instance(AbstractConnectionForm)

    def __init__(self, **kwargs):
        super(ProfileForm, self).__init__()
        self.manager = kwargs.pop('manager')
        if 'name' in kwargs:
            self.name = kwargs.pop('name')
        if 'driver_type' in kwargs:
            self.driver_type = kwargs.pop('driver_type')
        if 'driver' in kwargs:
            self.driver = kwargs.pop('driver')
        form_class = FORMS.get(self.driver_type, None)
        if form_class:
            self.connection_form = form_class(**kwargs)

    def dict(self):
        """ Return the informations of the form as a dict

        """
        infos = {'name': self.name, 'driver_type': self.driver_type,
                 'driver': self.driver}
        if self.connection_form:
            infos.update(self.connection_form.connection_dict())
        return infos

    def _observe_driver_type(self, change):
        """Build the list of driver matching the selected type and select the
        right connection_form

        """
        new_type = change['value']
        if new_type:
            driver_list = self.manager.matching_drivers([new_type])
            self.drivers = sorted(driver_list)
            form_class = FORMS.get(change['value'], None)
            if form_class:
                self.connection_form = form_class()
