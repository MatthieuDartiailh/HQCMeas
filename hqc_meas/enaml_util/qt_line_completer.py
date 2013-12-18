# -*- coding: utf-8 -*-

from atom.api import List, Tuple, Str, Bool, Callable, observe
from enaml.core.declarative import d_
from enaml.qt import QtCore, QtGui
from enaml.widgets.api import RawWidget


class QtLineCompleter(RawWidget):
    """ Simple style text editor, which displays a text field.
    """
    text = d_(Str())
    entries = d_(List())
    entries_updater = d_(Callable())
    delimiters = d_(Tuple(Str(), ('{','}')))
    hug_width = 'ignore'
    _no_update = Bool(False)

    def create_widget(self, parent):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        widget = CompleterLineEdit(parent, self.delimiters,
                                    self.entries, self.entries_updater)
        widget.setText(self.text)
        widget.textEdited.connect(self.update_object)
        return widget

    #---------------------------------------------------------------------------
    #  Handles the user entering input data in the edit control:
    #---------------------------------------------------------------------------

    def update_object ( self ):
        """ Handles the user entering input data in the edit control.
        """
        if (not self._no_update) and self.activated :
            try:
                value = self.get_widget().text()
            except AttributeError:
                value = self.get_widget().toPlainText()
            
            self._no_update = True
            self.text = value
            self._no_update = False
            
    #---------------------------------------------------------------------------
    #  Updates the editor when the object trait changes external to the editor:
    #---------------------------------------------------------------------------
    @observe('text')
    def update_widget (self, change):
        """ Updates the editor when the object trait changes externally to the
            editor.
        """
        if (not self._no_update) and self.get_widget() :
            self._no_update = True
            self.get_widget().setText(change['value'])
            self._no_update = False

class CompleterLineEdit(QtGui.QLineEdit):
    """
    """
    completionNeeded = QtCore.Signal(str)

    def __init__(self, parent, delimiters, entries, entries_updater):

        self.delimiters = delimiters

        super(CompleterLineEdit, self).__init__(parent)
        self.textChanged[str].connect(self.text_changed)
        self.completer = QtGui.QCompleter(self)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.completer.setModel(QtGui.QStringListModel(entries,self.completer))
        
        self.completionNeeded.connect(self.completer.complete)
        self.completer.activated[str].connect(self.complete_text)
        self.completer.setWidget(self)

        self._upddate_entries = True
        self.editingFinished.connect(self.on_editing_finished)
        self.entries_updater = entries_updater

    def text_changed(self, text):
        """
        """
        if self._upddate_entries and self.entries_updater:
            entries = self.entries_updater()
            self.completer.setModel(
                                QtGui.QStringListModel(entries,self.completer)
                                   )
            self._upddate_entries = False
        
        all_text = unicode(text)
        text = all_text[:self.cursorPosition()]
        split = text.split(self.delimiters[0])
        prefix = split[-1].strip()

        if len(split) > 1:
            self.completer.setCompletionPrefix(prefix)
            self.completionNeeded.emit(prefix)

        self.string = text

    def complete_text(self, text):
        """
        """
        cursor_pos = self.cursorPosition()
        before_text = unicode(self.text())[:cursor_pos]
        after_text = unicode(self.text())[cursor_pos:]
        prefix_len = len(before_text.split(self.delimiters[0])[-1].strip())

        if after_text.startswith(self.delimiters[1]):
            self.setText(before_text[:cursor_pos - prefix_len] + text +
                            after_text)
        else:
            self.setText(before_text[:cursor_pos - prefix_len] + text +
                        self.delimiters[1] + after_text)

        self.string = before_text[:cursor_pos - prefix_len] + text +\
                        self.delimiters[1] + after_text

        self.setCursorPosition(cursor_pos - prefix_len + len(text) + 2)
        self.textEdited.emit(self.string)

    def on_editing_finished(self):
        self._upddate_entries = True