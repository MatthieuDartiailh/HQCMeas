# -*- coding: utf-8 -*-

from atom.api import (Atom, List, Str, Unicode, Bool, observe)
from enaml.widgets.api import FileDialog
import enaml
with enaml.imports():
    from .saver_view import (TemplateSaverView, ScintillaDialog)
    
import os.path
from textwrap import wrap
from configobj import ConfigObj

class TemplateTaskSaver(Atom):
    """
    """
    template_folder = Unicode(os.path.normpath(
                                os.path.join(os.path.dirname(__file__),
                                             '../tasks/templates'))
                                             )
    template_tasks = List(Unicode())

    template_filename = Str()
    template_doc = Str()
    ok_ready = Bool(False)

    show_result = Bool(False)

    def _default_template_tasks(self):
        """
        """
        #sorted files only
        path = self.template_folder
        tasks = sorted(f for f in os.listdir(path)
                           if (os.path.isfile(os.path.join(path, f))
                           and f.endswith('.ini')))
        return tasks
        
    def _observe_template_filename(self, change):
        """
        """
        if change['value'] in self.template_tasks:
            path = os.path.join(self.template_folder, change['value'])
            doc_list = [com[1:].strip() 
                            for com in ConfigObj(path).initial_comment]
            self.template_doc = '\n'.join(doc_list)

    @observe('template_filename', 'template_doc')
    def _ready_to_save(self, change):
        """
        """
        if self.template_doc != '' and self.template_filename != '':
            self.ok_ready = True
        else:
            self.ok_ready = False

def save_task(task, mode):
    """
    """
    full_path = u''
    if mode == 'template':
        saver = TemplateTaskSaver()
        saver_dialog = TemplateSaverView(model = saver)
        
        if saver_dialog.exec_():
            if saver.template_filename.endswith('.ini'):
                full_path = os.path.join(saver.template_folder,
                                         saver.template_filename)
            else:
                full_path = os.path.join(saver.template_folder,
                                     saver.template_filename + '.ini')
        else:
            return
                                     
    elif mode == 'file':
        full_path = FileDialog(mode = 'save_file',
                          filters = [u'*.ini']).exec_()
        if not full_path:
            return
        
    task.update_preferences_from_members()
    preferences = task.task_preferences

    if mode == 'config':
        return preferences
    
    else:
        # Create an empty ConfigObj and set filename after so that the data are 
        # not loaded. Otherwise merge might lead to corrupted data.
        config = ConfigObj(indent_type = '    ')
        config.filename = full_path
        config.merge(preferences)
    
        if mode == 'template':
            config.initial_comment = wrap(saver.template_doc, 80)
        
        config.write()
    
        if mode == 'template':
            if saver.show_result:
                with open(full_path) as f:
                    t = '\n'.join(f.readlines())
                    ScintillaDialog(text = t).exec_()               