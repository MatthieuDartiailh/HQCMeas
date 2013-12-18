# -*- coding: utf-8 -*-
"""
Created on Sun Nov 03 17:22:39 2013

@author: Matthieu
"""

from atom.api import (Atom, List, Unicode, Instance, observe)
import enaml
with enaml.imports():
    from enaml.stdlib.message_box import critical, information

from textwrap import fill
from inspect import cleandoc

from .drivers import DRIVERS, DRIVER_TYPES, InstrIOError
from .forms import AbstractConnectionForm, FORMS, VisaForm

class InstrumentForm(Atom):
    """
    Simple UI panel used to display, create or edit an instrument profile

    Parameters
    ----------
    **kwargs
        Keyword arguments used to initialize attributes and form attributes

    Attributes
    ----------
    name : str
        Name of the instrument used to identify him. Should be different from
        the driver name
    driver_type : str
        Kind of driver to use, ie which kind of standard is used for communicate
    driver_list : list(Unicodestr)
        List of known driver matching `driver_type`
    driver : str
        Name of the selected driver
    connection_form : instance(AbstractConnectionForm)
        Form used to display the informations specific to the `driver_type`


    """
    name = Unicode('')
    driver_type = Unicode('')
    driver_list = List(Unicode(),[])
    driver = Unicode('')
    connection_form = Instance(AbstractConnectionForm)

    def __init__(self, *args, **kwargs):
        super(InstrumentForm, self).__init__(*args)
        if 'name' in kwargs:
            self.name = kwargs.pop('name')
        if 'driver_type' in kwargs:
            self.driver_type = kwargs.pop('driver_type')
        if 'driver' in kwargs:
            self.driver = kwargs.pop('driver') 
        self.connection_form = FORMS.get(self.driver_type, VisaForm)(**kwargs)

    @observe('driver_type')
    def _new_driver_type(self, change):
        """Build the list of driver matching the selected type and select the
        right connection_form

        """
        new_type = change['value']
        if new_type:
            driver_list = []
            driver_base_class = DRIVER_TYPES[change['value']]
            for driver_name, driver_class in DRIVERS.items():
                if issubclass(driver_class, driver_base_class):
                    driver_list.append(driver_name)
            self.driver_list = sorted(driver_list)
            self.connection_form = FORMS.get(change['value'], VisaForm)()
            
class InstrumentFormDialogHandler(Atom):
    """Handler for the UI of an `InstrumentForm` instance

    Before closing the `InstrumentForm` UI instance ensure that the informations
    provided allow to open the connection to the specified instrument.

    """
    
    def close(self, view, is_ok):
        model = view.instr
        connection_form = model.connection_form
        if is_ok:
            if (model.name != '' and model.driver_type and model.driver != ''
                and connection_form.check()):
                connection_dict = connection_form.connection_dict()
                try:
                    instr = DRIVERS[model.driver](connection_dict)
                    instr.close_connection()
                except InstrIOError:
                    message = cleandoc(u"""The software failed to
                                establish the connection with the instrument
                                please check all parameters and instrument state
                                and try again""")

                    critical(parent = view,
                             text = fill(message, 80),
                             title = 'Connection failure')

                view.result = True
                view.close()

            else:
                message = cleandoc(u"""You must fill the fields : name,
                       driver type, driver, {} before
                       validating""".format(connection_form.required_fields())
                                       )
                information(parent = view, text = fill(message, 80),
                          title = 'Missing information')

        else:
            view.close()