# -*- coding: utf-8 -*-

from traits.api import (HasTraits, List, Str, File, Directory, Button, Bool,
                        on_trait_change)
from traitsui.api import (View, VGroup, HGroup, UItem, ListStrEditor, Label,
                          CodeEditor, Handler, Spring)

import os
from configobj import ConfigObj

module_path = os.path.dirname(__file__)

class TemplateTaskSaverHandler(Handler):
    """
    """
    def object_ok_button_changed(self, info):
        """
        """
        info.ui.result = True
        info.ui.dispose()

    def object_cancel_button_changed(self, info):
        """
        """
        info.ui.result = False
        info.ui.dispose()

class TemplateTaskSaver(HasTraits):
    """
    """
    template_folder = Directory(os.path.join(module_path,'tasks/templates'))
    template_tasks = List(File)

    template_filename = Str()
    template_doc = Str()

    show_result = Bool(False)
    result = Str

    ok_button = Button('OK')
    ok_ready = Bool(False)
    cancel_button = Button('Cancel')

    traits_view = View(
                    VGroup(
                        HGroup(
                            UItem('template_tasks',
                                      editor = ListStrEditor(
                                                  editable = False,
                                                  title = 'Existing templates'),
                                  ),
                            VGroup(
                                HGroup(
                                    Label('Filename'),
                                    UItem('template_filename'),
                                    ),
                                Label('Description'),
                                UItem('template_doc', style = 'custom'),
                                label = 'New template info'
                                ),
                            ),
                        HGroup(
                            Label('Show result'),
                            UItem('show_result'),
                            Spring(),
                            UItem('ok_button', enabled_when = 'ok_ready'),
                            UItem('cancel_button'),
                        ),
                    ),
                    kind = 'livemodal',
                    title = 'Save template ?',
                    handler = TemplateTaskSaverHandler(),
                    )

    result_view = View(UItem('result', editor = CodeEditor()),
                       kind = 'modal', title = 'Resulting template file')

    def save_template(self, task):
        """
        """
        ui = self.edit_traits()
        if ui.result:
            if '.ini' not in self.template_filename:
                full_path = os.path.join(self.template_folder,
                                         self.template_filename + '.ini')
            else:
                full_path = os.path.join(self.template_folder,
                                         self.template_filename)
            config = ConfigObj(full_path, indent_type = '    ')
            task.update_preferences()
            preferences = task.task_preferences
            config.merge(preferences)
            config.write()
            if self.show_result:
                with open(full_path) as f:
                    self.result = f.read()
                self.edit_traits(view = 'result_view')

    def _template_tasks_default(self):
        """
        """
        #sorted files only
        path = self.template_folder
        tasks = sorted(f for f in os.listdir(path)
                           if (os.path.isfile(os.path.join(path, f))
                           and f.endswith('.ini')))
        return tasks

    @on_trait_change('template_filename, template_doc')
    def _ready_to_save(self):
        if self.template_doc != '' and self.template_filename != '':
            self.ok_ready = True
        else:
            self.ok_ready = False