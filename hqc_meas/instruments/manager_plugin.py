# -*- coding: utf-8 -*-
#==============================================================================
# module : instrument_manager.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from atom.api import Callable, Str
from enaml.core.declarative import Declarative, d_

from watchdog.observers import Observer
from watchdog.observers.api import ObservedWatch
from watchdog.events import (FileSystemEventHandler, FileCreatedEvent,
                             FileDeletedEvent, FileMovedEvent)

from ..enaml_util.pref_plugin import HasPrefPlugin


class InstrManagerPlugin(HasPrefPlugin):
    """
    """

    def start(self):
        """
        """

    def stop(self):
        """
        """

    def


class InstrUser(Declarative):
    """Extension to the 'instr_users' extensions point of the ManagerPlugin.

    Attributes
    ----------
    release_method: callable
        Callable to use when the ManagerPlugin needs to get a instrument
        profile back from its current user.

    default_policy:
        Does by default the user allows the manager to get the profile back
        when needed.

    """
    release_method = d_(Callable())

    default_policy = d_(Str())

# use Forward Typed to keep file more readable
class _FileListUpdater(FileSystemEventHandler):
    """Simple `watchdog` handler used for auto-updating the profiles list
    """
    def __init__(self, handler):
        self.handler = handler

    def on_created(self, event):
        super(_FileListUpdater, self).on_created(event)
        if isinstance(event, FileCreatedEvent):
            self.handler()

    def on_deleted(self, event):
        super(_FileListUpdater, self).on_deleted(event)
        if isinstance(event, FileDeletedEvent):
            self.handler()

    def on_moved(self, event):
        super(_FileListUpdater, self).on_deleted(event)
        if isinstance(event, FileMovedEvent):
            self.handler()
