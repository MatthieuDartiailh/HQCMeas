# -*- coding: utf-8 -*-
# =============================================================================
# module : profile_form.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""

from atom.api import (Atom, List, Str, Unicode, Instance, Typed, Value)

from .forms.base_forms import AbstractConnectionForm
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
    connection_form_view = Value()

    def __init__(self, **kwargs):
        super(ProfileForm, self).__init__()
        self.manager = kwargs.pop('manager')
        if 'name' in kwargs:
            self.name = kwargs.pop('name')
        if 'driver_type' in kwargs:
            self.driver_type = kwargs.pop('driver_type')
        if 'driver' in kwargs:
            self.driver = kwargs.pop('driver')

        if self.driver or self.driver_type:
            aux = self.driver if self.driver else self.driver_type
            form_class, view = self.manager.matching_form(aux, view=True)
            if form_class:
                if self.driver:
                    aux, _ = self.manager.drivers_request([self.driver])
                    self.connection_form = form_class(driver=aux[self.driver],
                                                      **kwargs)
                else:
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
        """Build the list of driver matching the selected type.

        """
        new_type = change['value']
        if new_type:
            driver_list = self.manager.matching_drivers([new_type])
            self.drivers = sorted(driver_list)

            form_class, view = self.manager.matching_form(new_type, view=True)
            if form_class:
                self.connection_form = form_class()
                self.connection_form_view = view
            else:
                self.connection_form = None
                self.connection_form_view = None

    def _observe_driver(self, change):
        """ Select the right connection_form for the selected driver.

        """
        driver = change['value']
        if driver:
            form_class, view = self.manager.matching_form(driver, view=True)
            aux, _ = self.manager.drivers_request([driver])
            if form_class:
                if isinstance(self.connection_form, form_class):
                    self.connection_form.driver = aux[driver]
                else:
                    self.connection_form = form_class(driver=driver)
                self.connection_form_view = view
            else:
                self.connection_form = None
                self.connection_form_view = None
