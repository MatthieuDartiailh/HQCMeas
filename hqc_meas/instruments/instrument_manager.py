# -*- coding: utf-8 -*-
#==============================================================================
# module : instrument_manager.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
This module defines the tools used to manage instruments.

Instruments connection's informations are stored in .ini files in the profiles
folder. The instrument manager provides a GUI to create and edit profiles and
also capabilities to filter through the available profiles.

:Contains:
    InstrumentManager
        Main class of the module, the only one which needs to be exported
    InstrumentManagerHandler
        Handler for the UI of the `InstrumentManager`
    InstrumentForm
        UI block used when displaying, creating or editing a profile
    InstrumentFormHandler
        Handler for the UI of the `InstrumentForm`
    FileListUpdater
        `watchdog` handler subclass to automatically update the list of profiles
    MODULE_PATH
        Path to this module

"""
from atom.api import (Atom, Dict, Unicode, Instance, Typed, observe)
import enaml
with enaml.imports():
    from enaml.stdlib.message_box import question
    from .instrument_form_view import InstrumentFormDialog

import os
from configobj import ConfigObj
from textwrap import fill
from inspect import cleandoc

from watchdog.observers import Observer
from watchdog.observers.api import ObservedWatch
from watchdog.events import (FileSystemEventHandler, FileCreatedEvent,
                            FileDeletedEvent, FileMovedEvent)

from .instrument_form import InstrumentForm

MODULE_PATH = os.path.dirname(__file__)

class FileListUpdater(FileSystemEventHandler):
    """Simple `watchdog` handler used for auto-updating the profiles list
    """
    def __init__(self, handler):
        self.handler = handler

    def on_created(self, event):
        super(FileListUpdater, self).on_created(event)
        if isinstance(event, FileCreatedEvent):
            self.handler()

    def on_deleted(self, event):
        super(FileListUpdater, self).on_deleted(event)
        if isinstance(event, FileDeletedEvent):
            self.handler()

    def on_moved(self, event):
        super(FileListUpdater, self).on_deleted(event)
        if isinstance(event, FileMovedEvent):
            self.handler()

class InstrumentManager(Atom):
    """
    Main object used to manage the instrument profile and filter them

    Attributes
    ----------
    instr_folder : directory path
        Path in which the profiles are stored.
    instrs : dict(str, path)
        Dict mapping profile names to the associated filename
    selected_instr_name : str
        Name of the selected instrumen profile
    selected_instr_form : instance(`InstrumentForm`)
        `InstrumentForm` instance associated to the selected profile
    observer, event_handler, watch
        `watchdog` objects ensuring that the list of profiles stays up to date

    """

    instr_folder = Unicode(os.path.join(MODULE_PATH, 'profiles'))
    instrs = Dict(Unicode(), Unicode())
    selected_instr_name = Unicode()
    selected_instr_form = Instance(InstrumentForm)

    observer = Typed(Observer,())
    event_handler = Typed(FileListUpdater)
    watch = Typed(ObservedWatch)

    def __init__(self, *args, **kwargs):
        super(InstrumentManager, self).__init__(*args, **kwargs)
        self.event_handler = FileListUpdater(self._update_instr_list)
        self.watch = self.observer.schedule(self.event_handler,
                                            self.instr_folder)
        self.observer.start()
        self._update_instr_list()
        if self.instrs:
            self.selected_instr_name = self.instrs.keys()[0]

    @observe('selected_instr_name')
    def _new_selected_instr(self, change):
        """Create a form for the selected instrument
        """
        path = self.instr_folder
        instr_file = self.instrs[change['value']]
        fullpath = os.path.join(path, instr_file)
        instr_dict = ConfigObj(fullpath).dict()
        instr_dict['name'] = change['value']
        self.selected_instr_form = InstrumentForm(**instr_dict)

    def _update_instr_list(self):
        """Update the list of profiles. Use as handle method for watchdog.
        """
        # sorted files only
        path = self.instr_folder
        instrs_filename = sorted(f for f in os.listdir(path)
                           if (os.path.isfile(os.path.join(path, f))
                           and f.endswith('.ini')))
        instrs = {}
        for instr_filename in instrs_filename:
            instr_name = self._normalise_name(instr_filename)
            instrs[instr_name] = instr_filename

        self.instrs = instrs

    @staticmethod
    def _normalise_name(name):
        """Normalize the name of the profiles by replacing '_' by spaces,
        removing the extension, and adding spaces between 'aA' sequences.
        """
        if name.endswith('.ini') or name.endswith('Task'):
            name = name[:-4] + '\0'
        aux = ''
        for i, char in enumerate(name):
            if char == '_':
                aux += ' '
                continue

            if char != '\0':
                if char.isupper() and i!=0 :
                    if name[i-1].islower():
                        if name[i+1].islower():
                            aux += ' ' + char.lower()
                        else:
                            aux += ' ' + char
                    else:
                        if name[i+1].islower():
                            aux += ' ' + char.lower()
                        else:
                            aux += char
                else:
                    if i == 0:
                        aux += char.upper()
                    else:
                        aux += char
        return aux

class InstrumentManagerHandler(Atom):
    """Handler for the UI of an `InstrumentManager` instance

    Methods
    -------
    object_add_instr_changed :
        If the user clicked the 'OK' button of the `InstrumentForm`, save the
        new profile
    object_edit_instr_changed :
        If the user clicked the 'OK' button of the `InstrumentForm`, save the
        edited profile
    object_delete_instr_changed :
        Prompt a confirmation dialo.

    """

    def add_instr_clicked(self, view):
        """
        Open a dialog to create a new profile and save it if the user close the
        dialog by cicking the 'OK' button.

        """
        instr_form = InstrumentForm()
        result = InstrumentFormDialog(instr_form = instr_form,
                                      mode = 'new').exec_()
        manager = view.manager
        if result:
            path = os.path.abspath(manager.instr_folder)
            filename = instr_form.name + '.ini'
            fullpath = os.path.join(path, filename)
            instr_config = ConfigObj(fullpath)
            instr_config['driver_type'] = instr_form.driver_type
            instr_config['driver'] = instr_form.driver
            instr_config.update(instr_form.connection_form.connection_dict())
            instr_config.write()

    def edit_instr_clicked(self, view):
        """
        Open a dialog to edit a profile and save the modifications if the user
        close the dialog by cicking the 'OK' button.

        """
        manager = view.manager
        instr_form = manager.selected_instr_form
        result = InstrumentFormDialog(instr_form = instr_form,
                                      mode = 'edit').exec_()
        if result:
            instr_file = manager.instrs[manager.selected_instr_name]
            path = os.path.abspath(manager.instr_folder)
            fullpath = os.path.join(path, instr_file)
            instr_config = ConfigObj(fullpath)
            instr_config['driver_type'] = instr_form.driver_type
            instr_config['driver'] = instr_form.driver
            instr_config.update(instr_form.connection_form.connection_dict())
            instr_config.write()

    def delete_instr_clicked(self, view):
        """
        Open confirmation dialog when the user asks to delete a profile
        """
        manager = view.manager
        message = cleandoc(u"""Are you sure want to delete this
                        instrument connection informations ?""")
        result = question(parent = view, text = fill(message, 80),
                title = 'Deletion confirmation' )
        if result is not None and result.action == 'accept':
            instr_file = manager.instrs[manager.selected_instr_name]
            path = os.path.abspath(manager.instr_folder)
            fullpath = os.path.join(path, instr_file)
            os.remove(fullpath)

def matching_instr_list(driver_key):
    """Return a list of instrument whose driver match the argument
    """
    manager = InstrumentManager()
    profile_dict = {}
    for profile in manager.instrs:
        path = os.path.join(manager.instr_folder, manager.instrs[profile])
        if driver_key == ConfigObj(path)['driver']:
            profile_dict[profile] = path

    return profile_dict