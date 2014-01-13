# -*- coding: utf-8 -*-

from atom.api import Str, observe
from enaml.core.declarative import d_
from enaml.qt import QtGui
from enaml.widgets.api import RawWidget


class QtAutoScrollMultilineDisplay(RawWidget):
    """ Simple style text editor, which displays a text field.
    """
    text = d_(Str())
    hug_width = 'ignore'

    def create_widget(self, parent):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        widget = QtGui.QTextEdit(parent)
        widget.setReadOnly(True)
        widget.setText(self.text)
        return widget
            
    @observe('text')
    def update_widget (self, change):
        """ Updates the editor when the object trait changes externally to the
            editor.
        """
        widget = self.get_widget()
        if  widget:
            widget.setText(change['value'])
            widget.moveCursor(QtGui.QTextCursor.End)