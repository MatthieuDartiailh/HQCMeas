# -*- coding: utf-8 -*-
# =============================================================================
# module : pulses/manager/config/base_config.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""

"""
from atom.api import (Atom, Str, Bool, Subclass, ForwardTyped,
                      observe)

from inspect import getdoc, cleandoc

from ..items.item import Item


# Circular import protection
def pulses_manager():
    from ..manager_plugin import TaskManagerPlugin
    return TaskManagerPlugin


class AbstractConfig(Atom):
    """ Base class for task configurer.

    """
    #: Pulses manager, necessary to retrieve item(pulse/sequence)
    #: implementations.
    manager = ForwardTyped(pulses_manager)

    #: Class of the item to create.
    item_class = Subclass(Item)

    # Bool indicating if the build can be done.
    config_ready = Bool(False)

    def check_parameters(self, change):
        """Check if enough parameters have been provided to build the item.

        This methodd should fire the config_ready event each time it is called
        sending True if everything is allright, False otherwise.

        """
        err_str = '''This method should be implemented by subclasses of
        AbstractConfig. This method is called each time a member is changed
        to check if enough parameters has been provided to build the item.'''
        raise NotImplementedError(cleandoc(err_str))

    def build_item(self):
        """This method use the user parameters to build the item object

         Returns
        -------
        item : Item
            Item object built using the user parameters. Ready to be
            inserted in a sequence.

        """
        err_str = '''This method should be implemented by subclasses of
        AbstractConfig. This method is called when the user validate its
        choices and that the item must be built.'''
        raise NotImplementedError(cleandoc(err_str))


class PulseConfig(AbstractConfig):
    """

    """

    # Docstring of the class to help pepole know what they are going to create.
    task_doc = Str()

    def __init__(self, **kwargs):
        super(PulseConfig, self).__init__(**kwargs)
        self.task_doc = getdoc(self.task_class).replace('\n', ' ')

    def build_task(self):
        return self.task_class(task_name=self.task_name)

    @observe('task_name')
    def check_parameters(self, change):
        """ Observer notifying that the configurer is ready to build.

        """
        if self.task_name != '':
            self.config_ready = True
        else:
            self.config_ready = False


class SequenceConfig(AbstractConfig):
    """

    """
    pass
