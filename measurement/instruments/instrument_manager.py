# -*- coding: utf-8 -*-
"""
"""
from traits.api import (HasTraits, List, Dict, Str, File, Directory,
                        Instance, Button, on_trait_change)
from traitsui.api import (View, VGroup, HGroup, UItem, ListStrEditor, VGrid,
                          Label, OKCancelButtons, Handler, EnumEditor, error,
                          InstanceEditor)

import os, re
from configobj import ConfigObj
from textwrap import fill
from inspect import cleandoc

from watchdog.observers import Observer
from watchdog.observers.api import ObservedWatch
from watchdog.events import (FileSystemEventHandler, FileCreatedEvent,
                            FileDeletedEvent, FileMovedEvent)

from .drivers import DRIVERS, DRIVER_TYPES, InstrIOError
from connection_forms import AbstractConnectionForm, FORMS, VisaForm

MODULE_PATH = os.path.dirname(__file__)

class FileListUpdater(FileSystemEventHandler):
    """
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

class InstrumentFormHandler(Handler):
    """
    """
    def close(self, info, is_ok):
        model = info.object
        if is_ok:
            if (model.name != '' and model.driver_type and model.driver != ''
                and model.form.check()):
                connection_dict = model.form.connection_dict()
                try:
                    instr = DRIVERS[model.driver](connection_dict)
                    instr.close_connection()
                except InstrIOError:
                    message = cleandoc("""The software failed to
                                establish the connection with the instrument
                                please check all parameters and instrument state
                                and try again""")

                    error(message = fill(message, 80),
                          title = 'Connection failure', buttons = ['OK'],
                          parent = info.ui.control)
                    return False

                return True

            else:
                message = cleandoc("""You must fill the fields : name,
                           driver type, driver, {} before
                           validating""".format(model.form.required_fields())
                                       )
                error(message = fill(message, 80),
                          title = 'Missing information', buttons = ['OK'],
                          parent = info.ui.control)
        else:
            return True

class InstrumentForm(HasTraits):
    """
    """
    name = Str('')
    driver_type = Str()
    driver_list = List(Str)
    driver = Str('')
    form = Instance(AbstractConnectionForm, VisaForm())

    traits_view = View(
                    VGroup(
                        VGrid(
                            Label('Name'), UItem('name',
                                                        style = 'readonly'),
                            Label('Driver type'), UItem('driver_type',
                                                        style = 'readonly'),
                            Label('Driver'), UItem('driver',
                                                        style = 'readonly'),
                            ),
                        UItem('form', style = 'custom'),
                    ),
                )

    edit_view = View(
                    VGroup(
                        VGrid(
                            Label('Name'), UItem('name', style = 'readonly'),
                            Label('Driver type'), UItem('driver_type',
                                                editor = EnumEditor(
                                                values = DRIVER_TYPES.keys())),
                            Label('Driver'), UItem('driver',
                                                editor = EnumEditor(
                                                    name = 'driver_list')),
                            ),
                        UItem('form@',
                                  editor = InstanceEditor(view = 'edit_view'))
                    ),
                    buttons = OKCancelButtons,
                    handler = InstrumentFormHandler(),
                    title = 'Edit instrument info',
                    kind = 'modal',
                    width = 250,
                )

    new_view = View(
                    VGroup(
                        VGrid(
                            Label('Name'), UItem('name'),
                            Label('Driver type'), UItem('driver_type',
                                                editor = EnumEditor(
                                                values = DRIVER_TYPES.keys())),
                            Label('Driver'), UItem('driver',
                                                editor = EnumEditor(
                                                    name = 'driver_list')),
                            ),
                        UItem('form@',
                                  editor = InstanceEditor(view = 'edit_view'))
                    ),
                    buttons = OKCancelButtons,
                    handler = InstrumentFormHandler(),
                    title = 'Create instrument info',
                    kind = 'modal',
                    width = 250,
                )

    def __init__(self, *args, **kwargs):
        super(InstrumentForm, self).__init__(*args, **kwargs)
        self.form = FORMS.get(self.driver_type, VisaForm)(**kwargs)

    @on_trait_change('driver_type')
    def _new_driver_type(self, new):
        """
        """
        driver_list = []
        driver_base_class = DRIVER_TYPES[new]
        for driver_name, driver_class in DRIVERS.items():
            if issubclass(driver_class, driver_base_class):
                driver_list.append(driver_name)
        self.driver_list = driver_list
        self.form = FORMS.get(new, VisaForm)()


class InstrumentManagerHandler(Handler):
    """
    """

    def object_add_instr_changed(self, info):
        """
        """
        instr = InstrumentForm()
        instr_ui = instr.edit_traits(view = 'new_view',
                                       parent = info.ui.control)
        if instr_ui.result:
            path = os.path.abspath(info.object.instr_folder)
            filename = instr.name + '.ini'
            fullpath = os.path.join(path, filename)
            instr_config = ConfigObj(fullpath)
            instr_config['driver_type'] = instr.driver_type
            instr_config['driver'] = instr.driver
            instr_config.update(instr.form.connection_dict())
            instr_config.write()

    def object_edit_instr_changed(self, info):
        """
        """
        model = info.object
        instr = model.selected_instr
        instr_ui = instr.edit_traits(view = 'edit_view',
                                       parent = info.ui.control)
        if instr_ui.result:
            instr_file = model.instrs[model.selected_instr_name]
            path = os.path.abspath(info.object.instr_folder)
            fullpath = os.path.join(path, instr_file)
            instr_config = ConfigObj(fullpath)
            instr_config['driver_type'] = instr.driver_type
            instr_config['driver'] = instr.driver
            instr_config.update(model.selected_instr.form.connection_dict())
            instr_config.write()

    def object_delete_instr_changed(self, info):
        """
        """
        model = info.object
        message = cleandoc("""Are you sure want to delete this
                        instrument connection informations ?""")
        if error(message = fill(message, 80),
                title = 'Deletion confirmation',
                parent = info.ui.control):
            instr_file = model.instrs[model.selected_instr_name]
            path = os.path.abspath(info.object.instr_folder)
            fullpath = os.path.join(path, instr_file)
            os.remove(fullpath)

class InstrumentManager(HasTraits):
    """
    """

    instr_folder = Directory(os.path.join(MODULE_PATH, 'profiles'))
    instrs = Dict(Str, File)
    instrs_name = List(Str)
    selected_instr_name = Str
    selected_instr = Instance(InstrumentForm)

    add_instr = Button('Add')
    edit_instr = Button('Edit')
    delete_instr = Button('Delete')

    observer = Instance(Observer,())
    event_handler = Instance(FileListUpdater)
    watch = Instance(ObservedWatch)

    instrs_view = View(
                    HGroup(
                        UItem('instrs_name',
                              editor = ListStrEditor(
                                  selected = 'selected_instr_name'),
                              ),
                        UItem('selected_instr', style = 'custom'),
                        VGroup(
                            UItem('add_instr'),
                            UItem('edit_instr'),
                            UItem('delete_instr'),
                            ),
                        ),
                        handler = InstrumentManagerHandler()
                    )

    def __init__(self, *args, **kwargs):
        super(InstrumentManager, self).__init__(*args, **kwargs)
        self.event_handler = FileListUpdater(self._update_instr_list)
        self.watch = self.observer.schedule(self.event_handler,
                                            self.instr_folder)
        self.observer.start()

        self._update_instr_list()
        if self.instrs_name:
            self.selected_instr_name = self.instrs_name[0]

    def matching_instr_list(self, driver_key):
        """Return a list of instrument whose driver match the argument
        """
        profile_dict = {}
        for profile in self.instrs:
            path = os.path.join(self.instr_folder, self.instrs[profile])
            if driver_key == ConfigObj(path)['driver']:
                profile_dict[profile] = self.instrs[profile]

        return profile_dict

    @on_trait_change('selected_instr_name')
    def _new_selected_instr(self, new):
        """
        """
        path = self.instr_folder
        instr_file = self.instrs[new]
        fullpath = os.path.join(path, instr_file)
        instr_dict = ConfigObj(fullpath).dict()
        instr_dict['name'] = new
        self.selected_instr = InstrumentForm(**instr_dict)

    def _update_instr_list(self):
        """
        """
        # sorted files only
        path = self.instr_folder
        instrs_filename = sorted(f for f in os.listdir(path)
                           if (os.path.isfile(os.path.join(path, f))
                           and f.endswith('.ini')))
        instrs = {}
        instrs_name = []
        for instr_filename in instrs_filename:
            instr_name = self._normalise_name(instr_filename)
            instrs[instr_name] = instr_filename
            instrs_name.append(instr_name)

        self.instrs = instrs
        self.instrs_name = instrs_name

    def _normalise_name(self, name):
        """
        """
        name = re.sub('(?<!^[A-Z])(?=[A-Z])', ' ', name)
        name = re.sub('_', ' ', name)
        name = re.sub('^ ', '', name)
        name = re.sub('.ini', '', name)
        return name.capitalize()

if __name__ == "__main__":
    InstrumentManager().configure_traits()
