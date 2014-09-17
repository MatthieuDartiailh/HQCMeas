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
from atom.api import Atom, Typed, Value, Enum, Unicode, Property, set_default
from enaml.workbench.ui.api import Workspace
from enaml.widgets.api import FileDialogEx
from inspect import cleandoc
from textwrap import fill
from configobj import ConfigObj

from ..api import RootSequence

with enaml.imports():
    from enaml.stdlib.message_box import question, information
    from .checks.checks_display import ChecksDisplay
    from .content import SequenceSpaceContent, SequenceSpaceMenu
    from .dialogs import TemplateLoadDialog, TemplateSaveDialog


LOG_ID = u'hqc_meas.pulses.workspace'


class SequenceEditionSpaceState(Atom):
    """ Container object used to store the workspace state in the plugin.

    Using this avoid losing the currently edited sequence when switching
    workspaces and avoid crowding too much the plugin.

    """
    #: Currently edited sequence.
    sequence = Property()

    #: If this measure has already been saved is it a template or not.
    sequence_type = Enum('Unknown', 'Standard', 'Template')

    #: Path to the file in which the edited sequence should be saved.
    sequence_path = Unicode()

    #: Description of the sequence (only applyt o template).
    sequence_doc = Unicode()

    # --- Private API ---------------------------------------------------------

    _sequence = Typed(RootSequence)

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
            pass

        elif mode == 'file':
            factory = FileDialogEx.get_open_file_name
            path = ''
            if self.state.sequence_path:
                path = os.path.dirname(self.state.sequence_path)
            save_path = factory(self.content, current_path=path,
                                name_filters=['*.ini'])

            if save_path:
                self._save_to_file(self.state.sequence, save_path)

        elif mode == 'template':
            # Here must check context is TemplateContext and compilation is ok
            # (as template cannot be re-edited if not merged). Variable used
            # for compilation are cached.
            dial = TemplateSaveDialog(workspace=self)
            dial.exec_()

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
            pass

        elif mode == 'template':
            pass

        else:
            mess = cleandoc('''Invalid mode for load sequence : {}. Admissible
                            values are 'file' and 'template'.''')
            raise ValueError(mess.format(mode))

    def time_sequence_compilation(self, use_context=False):
        """ Time the compilation time of the currently edited sequence.

        This can be useful to check the sequence compile correctly before
        saving it. It will also give an idea if further optimisations (Cython)
        are needed to reach an acceptable speed.

        """
        pass

    # --- Private API ---------------------------------------------------------

    def _get_dock_area(self):
        if self.content and self.content.children:
            return self.content.children[0]

    @staticmethod
    def _save_to_file(sequence, path):
        """ Logic to save a sequence to file given a path.

        """
        config = ConfigObj()
        config.filename = path
        config.update(sequence.preferences_from_members())

        config.write()
