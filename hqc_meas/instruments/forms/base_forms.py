# -*- coding: utf-8 -*-
#==============================================================================
# module : connection_forms.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
Definition of the forms used to enter the information necessary to open a
connection to an instrument according to the type of connection used.

:Contains:
    AbstractConnectionForm : Abstract class defining the expected method for a
        form. Look at it when writing new forms.
    VisaForm : Form used for instruments using the VISA standard.
    FORMS : Dict mapping protocol names to the form to be used.
"""
from textwrap import fill
from inspect import cleandoc
from atom.api import Atom, Unicode


class AbstractConnectionForm(Atom):
    """
    Abstract class defining what is expected from a form

    Methods
    -------
    check()
        Check whether or not enough information have been given by the user.
        Called when the user attempt to press the ok button of the form he is
        editing.
    required_fields()
        Return a string listing the field that the user must fill. Called when
        the check method fail.
    connection_dict()
        Return a dictionnary holding all the necessary informations to open a
        connection with an instrument using the protocol for which the form was
        written. The keys must match the ones expected by the `BaseInstrument`
        subclass which will use it.

    """
    def check(self):
        """Check whether or not enough information have been given by the user.
        """
        msg = fill(cleandoc("""This  method should be implemented by classes
            subclassing AbstractConnectionForm. It must check whether or not
            the user gave enough information when filling the form"""), 80)
        raise NotImplementedError(msg)

    def required_fields(self):
        """Return a string listing the field that the user must fill. This list
        can be either static or match the fields the user did not fill
        correctly.

        """
        msg = fill(cleandoc("""This  method should be implemented by classes
            subclassing AbstractConnectionForm. It must return a string listing
            the required field or the ones incorrectly filled"""), 80)
        raise NotImplementedError(msg)

    def connection_dict(self):
        """Return a dictionnary holding all the necessary informations to open a
        connection with an instrument using the protocol for which the form was
        written.

        """
        msg = fill(cleandoc("""This  method should be implemented by classes
            subclassing AbstractConnectionForm. It must return a dictionnary
            holding all the necessary informations to open a connection with
            an instrument using the protocol for which the form was written.
            """), 80)
        raise NotImplementedError(msg)


class VisaForm(AbstractConnectionForm):
    """
    Form for instrument using the VISA standard for communication.

    Attributes
    ----------
    connection_type : {'GPIB', 'TCPIP', 'USB'}
        Communication bus to use
    address : str
        Address of the instrument (depends on the connection type)
    additionnal_mode : str
        Additionnal information for specifying a specific protocol should be
        used to open the connection. (ex : 'INSTR', '50000::SOCKET')

    Methods
    -------
    check()
        Check whether or not enough information have been given by the user.
        Called when the user attempt to press the ok button of the form he is
        editing.
    required_fields()
        Return a string listing the field that the user must fill. Called when
        the check method fail.
    connection_dict()
        Return a dictionnary holding all the necessary informations to open a
        connection with an instrument using the protocol for which the form was
        written. The keys msut match the ones expected by the `BaseInstrument`
        subclass which will use it.

    """

    connection_type = Unicode('')
    address = Unicode('')
    additionnal_mode = Unicode('')

    def check(self):
        """Check whether or not the user provided a type and an address.
        """
        return (self.connection_type != '' and self.address != '')

    def required_fields(self):
        """Return the mandatory fields for a Visa instrument
        """
        return 'connection type and address'

    def connection_dict(self):
        """Return the connection dictionnary which will be used by the
        `VisaInstrument` class to open a connection.
        """
        return {'connection_type': self.connection_type,
                'address': self.address,
                'additionnal_mode': self.additionnal_mode}


class DummyForm(AbstractConnectionForm):
    """
    """

    def check(self):
        """Check whether or not the user provided a type and an address.
        """
        return True

    def required_fields(self):
        """Return the mandatory fields for a Visa instrument
        """
        return ''

    def connection_dict(self):
        """Return the connection dictionnary which will be used by the
        `VisaInstrument` class to open a connection.
        """
        return {}

FORMS = {'Dummy': DummyForm, 'Visa': VisaForm}
"""Dictionnary mapping protocol names to their associated form. Used to
determine the correct form to display once the user selected a driver type

"""
