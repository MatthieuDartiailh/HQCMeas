# -*- coding: utf-8 -*-

from atom.api import Unicode, observe
from enaml.core.declarative import d_
from enaml.qt import QtGui
from enaml.widgets.api import RawWidget


class QtAutoscrollHtml(RawWidget):
    """ Custom Html display which scrolls down to the last line on update.

    """
    text = d_(Unicode())
    hug_width = 'ignore'
    hug_height = 'ignore'

    def create_widget(self, parent):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        widget = QtGui.QTextEdit(parent)
        widget.setReadOnly(True)
        widget.setHtml(self.text)
        return widget

    @observe('text')
    def update_widget(self, change):
        """ Updates the editor when the object trait changes externally to the
            editor.
        """
        widget = self.get_widget()
        if widget:
            widget.setHtml(change['value'])
            widget.moveCursor(QtGui.QTextCursor.End)
