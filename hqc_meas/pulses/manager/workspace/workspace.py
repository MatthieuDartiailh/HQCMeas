# -*- coding: utf-8 -*-
# =============================================================================
# module : hqc_meas/pulses/manager/workspace/workspace.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
import os
import enaml
from atom.api import (Atom, Typed, Value, Enum, Unicode, Property,
                      set_default)
from enaml.workbench.ui.api import Workspace
from enaml.widgets.api import FileDialogEx
from inspect import cleandoc
from textwrap import fill

from ...api import RootSequence
from ..sequences_io import save_sequence_prefs

with enaml.imports():
    from enaml.stdlib.message_box import question
    from .content import SequenceSpaceContent
    from .w_manifest import SequenceSpaceMenu
    from .dialogs import (TemplateLoadDialog, TemplateSaveDialog,
                          TypeSelectionDialog)


LOG_ID = u'hqc_meas.pulses.workspace'


class SequenceEditionSpaceState(Atom):
    """ Container object used to store the workspace state in the plugin.

    Using this avoid losing the currently edited sequence when switching
    workspaces and avoid crowding too much the plugin.

    """
    #: Currently edited sequence.
    sequence = Property()

    #: If this measure has already been saved,  is it a template or not ?
    sequence_type = Enum('Unknown', 'Standard', 'Template')

    #: Path to the file in which the edited sequence should be saved.
    sequence_path = Unicode()

    #: Description of the sequence (only applyt o template).
    sequence_doc = Unicode()

    # --- Private API ---------------------------------------------------------

    _sequence = Typed(RootSequence, ())

    def _get_sequence(self):
        return self._sequence

    def _set_sequence(self, value):
        """ Allow to perform clean up action when changing the sequence.

        Avoid the use of a static observer (disappear in Atom 1.0.0)

        """
        self.sequence_type = 'Unknown'
        self.sequence_path = u''
        self.sequence_doc = u''
        self._sequence = value


class SequenceEditionSpace(Workspace):
    """
    """
    # --- Public API ----------------------------------------------------------

    #: Refrence to the plugin.
    plugin = Value()

    #: Reference to the workspace state store in the plugin.
    state = Typed(SequenceEditionSpaceState)

    #: Reference to the log panel model received from the log plugin.
    log_model = Value()

    #: Getter for the dock area linked to the workspace.
    dock_area = Property()

    window_title = set_default('Pulses')

    def start(self):
        """
        """
        plugin = self.workbench.get_plugin(u'hqc_meas.pulses')
        plugin.workspace = self
        self.plugin = plugin
        if plugin.workspace_state:
            self.state = plugin.workspace_state
        else:
            state = SequenceEditionSpaceState()
            self.state = state
            plugin.workspace_state = state

        # Add handler to the root logger to display messages in panel.
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'hqc_meas.logging.add_handler'
        self.log_model = core.invoke_command(cmd,
                                             {'id': LOG_ID, 'mode': 'ui'},
                                             self)[0]

        # Create content.
        self.content = SequenceSpaceContent(workspace=self)

        # Contribute menus.
        self.workbench.register(SequenceSpaceMenu())

    def stop(self):
        """
        """
        # Remove handler from the root logger.
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'hqc_meas.logging.remove_handler'
        core.invoke_command(cmd, {'id': LOG_ID}, self)

        self.workbench.unregister(u'hqc_meas.pulses.workspace.menus')

        plugin = self.workbench.get_plugin(u'hqc_meas.pulses')
        plugin.workspace = None

    def new_sequence(self):
        """ Create a brand new empty sequence.

        """
        message = cleandoc("""Make sure you saved your modification to the
                        sequence you are editing before creating a new one.
                        Press OK to confirm, or Cancel to go back to editing
                        and get a chance to save it.""")

        result = question(self.content,
                          'Currently edited sequence replacement',
                          fill(message.replace('\n', ' '), 79),
                          )

        if result is not None and result.action == 'accept':
            self.state.sequence = RootSequence()

    def save_sequence(self, mode='default'):
        """ Save the currently edited sequence.

        Parameters
        ----------
        mode : {'default', 'file', 'template'}
            - default : save the sequence by using the state to determine the
            procedure to use.
            - file : save the sequence as a standard sequence and prompt the
            user to select a file.
            - template : save the sequence as a template sequence, prompt the
            user to choose a template name and give a documentation.

        """
        if mode == 'default':
            state = self.state
            if state.sequence_type == 'Unknown':
                # Here ask question and call save_sequence with right kind.
                dial = TypeSelectionDialog(self.content)
                dial.exec_()
                if dial.result:
                    self.save_sequence(dial.type)

            elif state.sequence_type == 'Standard':
                self._save_sequence_to_file(state.sequence_path)

            # Use else here as sequence_type is an enum.
            else:
                # Here stuff is a bit more complex as compilation checks need
                # to be performed.

                # Could implement TemplateSaveDialog as a wizard using a stack
                # widget here I would bypass the first item. This would avoid
                # code duplication and allow the user to change the compilation
                # vars (useful for loaded seq that will be identified but will
                # lack vars, might later implement a cache for this using
                # pickle)
                # The compilation part would win at being implemented with a
                # separate model and view, to be used in
                # time_sequence_compilation.

                dial = TemplateSaveDialog(self.content, workspace=self,
                                          step=1)
                dial.exec_()
                if dial.result:
                    s_ = self.state
                    self.state
                    self._save_sequence_to_template(s_.sequence_path,
                                                    s_.sequence_doc)

        elif mode == 'file':
            factory = FileDialogEx.get_save_file_name
            path = ''
            if self.state.sequence_path:
                path = os.path.dirname(self.state.sequence_path)
            save_path = factory(self.content, current_path=path,
                                name_filters=['*.ini'])

            if save_path:
                self._save_sequence_to_file(save_path)
                self.state.sequence_type = 'Standard'
                self.state.sequence_path = save_path

        elif mode == 'template':
            # Here must check context is TemplateContext and compilation is ok
            # (as template cannot be re-edited if not merged). Variable used
            # for compilation are cached.
            dial = TemplateSaveDialog(self.content, workspace=self)
            dial.exec_()
            if dial.result:
                self._save_sequence_to_template(dial.path, dial.doc)
                self.state.sequence_type = 'Template'
                self.state.sequence_path = dial.path
                self.state.sequence_doc = dial.doc

        else:
            mess = cleandoc('''Invalid mode for save sequence : {}. Admissible
                            values are 'default', 'file' and 'template'.''')
            raise ValueError(mess.format(mode))

    def load_sequence(self, mode='file'):
        """ Load an existing sequence to edit it.

        Parameters
        ----------
        mode : {'file', 'template'}
            - file : load a sequence from a file chosen by the user.
            - template : lod a sequence from a template chosen by the user.

        """
        if mode == 'file':
            factory = FileDialogEx.get_open_file_name
            path = ''
            if self.state.sequence_path:
                path = os.path.dirname(self.state.sequence_path)
            load_path = factory(self.content, current_path=path,
                                name_filters=['*.ini'])

            if load_path:
                seq = self._load_sequence_from_file(load_path)
                self.state.sequence_type = 'Standard'
                self.state.sequence_path = load_path
                self.state.sequence = seq
                self.state.ext_vars = seq.external_vars

        elif mode == 'template':
            dial = TemplateLoadDialog(self.content, workspace=self)
            dial.exec_()
            if dial.result:
                seq = self._load_sequence_template(dial.prefs)
                self.state.sequence_type = 'Template'
                self.state.sequence_path = dial.path
                self.state.sequence_doc = dial.doc
                self.state.sequence = seq
                self.state.ext_vars = seq.external_vars

        else:
            mess = cleandoc('''Invalid mode for load sequence : {}. Admissible
                            values are 'file' and 'template'.''')
            raise ValueError(mess.format(mode))

    # --- Private API ---------------------------------------------------------

    def _get_dock_area(self):
        if self.content and self.content.children:
            return self.content.children[0]

    def _save_sequence_to_file(self, path):
        seq = self.state.sequence
        prefs = seq.preferences_from_members()
        prefs['external_vars'] = repr(dict.fromkeys(seq.external_vars.keys(),
                                                    ''))
        save_sequence_prefs(path, prefs)

    def _save_sequence_to_template(self, path, doc):
        seq = self.state.sequence
        prefs = seq.preferences_from_members()
        prefs['external_vars'] = repr(dict.fromkeys(seq.external_vars.keys(),
                                                    ''))
        prefs['template_vars'] = prefs.pop('external_vars')
        del prefs['item_class']
        del prefs['time_constrained']
        save_sequence_prefs(path, prefs, doc)

    def _load_sequence_from_file(self, path):
        core = self.workbench.get_plugin('enaml.workbench.core')
        cmd = 'hqc_meas.pulses.build_sequence'
        return core.invoke_command(cmd, {'kind': 'file', 'path': path})

    def _load_sequence_from_template(self, prefs):
        prefs['external_vars'] = prefs.pop('template_vars')
        prefs['item_class'] = 'RootSequence'
        core = self.workbench.get_plugin('enaml.workbench.core')
        cmd = 'hqc_meas.pulses.build_sequence'
        return core.invoke_command(cmd, {'kind': 'file', 'prefs': prefs})
