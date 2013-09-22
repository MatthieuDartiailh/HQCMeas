# -*- coding: utf-8 -*-
from textwrap import fill
from inspect import cleandoc
from traits.api import HasTraits, Str
from traitsui.api import (View, UItem, VGrid,
                          Label,EnumEditor)

class AbstractConnectionForm(HasTraits):
    """
    """
    def check(self):
        """
        """
        msg = fill(cleandoc(""), 80)
        raise NotImplementedError(msg)

    def required_fields(self):
        """
        """
        msg = fill(cleandoc(""), 80)
        raise NotImplementedError(msg)

    def connection_dict(self):
        """
        """
        msg = fill(cleandoc(""), 80)
        raise NotImplementedError(msg)

class VisaForm(AbstractConnectionForm):
    """
    """
    connection_type = Str('')
    address = Str('')
    additionnal_mode = Str('')

    traits_view = View(
                VGrid(
                    Label('Connection'), UItem('connection_type',
                                                style = 'readonly'),
                    Label('Address'), UItem('address',
                                                style = 'readonly'),
                    Label('Additionnal'), UItem('additionnal_mode',
                                                style = 'readonly'),
                ),
            )

    edit_view = View(
                    VGrid(
                        Label('Connection'), UItem('connection_type',
                                editor = EnumEditor(
                                    values = ['GPIB', 'USB', 'TCPIP']),
                                    ),
                        Label('Address'), UItem('address'),
                        Label('Additionnal'), UItem('additionnal_mode'),
                    ),
                )

    new_view = View(
                    VGrid(
                        Label('Connection'), UItem('connection_type',
                                editor = EnumEditor(
                                    values = ['GPIB', 'USB', 'TCPIP']),
                                    ),
                        Label('Address'), UItem('address'),
                        Label('Additionnal'), UItem('additionnal_mode'),
                    ),
                )

FORMS = {'Visa' : VisaForm}