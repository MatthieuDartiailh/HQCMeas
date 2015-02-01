""" Enaml widget for editing a list of string
"""
# ------------------------------------------------------------------------------
#  Imports:
# ------------------------------------------------------------------------------
from atom.api import (Bool, List, observe, set_default, Unicode, Enum, Int)

from enaml.widgets.api import RawWidget
from enaml.core.declarative import d_
from enaml.qt.QtGui import QListWidget, QAbstractItemView

# cyclic notification guard flags
INDEX_GUARD = 0x1


class QtListStrWidget(RawWidget):
    """ A Qt4 implementation of an Enaml ProxyListStrView.

    """
    #: The list of str being viewed
    items = d_(List(Unicode()))

    #: The list of index of the currently selected str
    selected_index = d_(Int(-1))
    selected_indexes = d_(List(Int(), [-1]))

    #: The list of the currently selected str
    selected_item = d_(Unicode(''))
    selected_items = d_(List(Unicode(), ['']))

    #: Whether or not the user can select multiple lines
    multiselect = d_(Bool(False))

    #: List of operations the user can perform
    operations = d_(List(Enum('delete', 'insert', 'append', 'edit', 'move'),
                         ['delete', 'insert', 'append', 'edit', 'move']))

    #: .
    hug_width = set_default('strong')
    hug_height = set_default('ignore')

    #: Cyclic notification guard. This a bitfield of multiple guards.
    _guard = Int(0)

    __slots__ = ['__weakref__']

    #--------------------------------------------------------------------------
    # Initialization API
    # -------------------------------------------------------------------------
    def create_widget(self, parent):
        """ Create the QListView widget.

        """
        # Create the list model and accompanying controls:
        widget = QListWidget(parent)
        self.selected_index = -1
        self.selected_indexes = [-1]
        self.selected_item = ''
        self.selected_items = ['']
        for item in self.items:
            widget.addItem(item)
        if self.multiselect:
            mode = QAbstractItemView.ExtendedSelection
        else:
            mode = QAbstractItemView.SingleSelection
        widget.setSelectionMode(mode)
        widget.itemSelectionChanged.connect(self.on_selection)
        return widget

    # -------------------------------------------------------------------------
    # Signal Handlers
    # -------------------------------------------------------------------------
    def on_selection(self):
        """ The signal handler for the index changed signal.

        """
        widget = self.get_widget()
        items = self.items
        if not self._guard & INDEX_GUARD:
            indexes = [index.row() for index in widget.selectedIndexes()]
            if indexes:
                if self.multiselect:
                    self.selected_items = [items[i] for i in indexes]
                    self.selected_indexes = indexes
                else:
                    new_index = indexes[0]
                    self.selected_index = new_index
                    self.selected_item = items[new_index]

    def is_auto_add(self, index):
        """ Returns whether or not the index is the special 'auto add' item at
            the end of the list.
        """
        return (self.declarations.auto_add
                and (index >= self.widget._model.count()))

    #--------------------------------------------------------------------------
    # ProxyListStrView API
    #--------------------------------------------------------------------------

    def set_items(self, items):
        """
        """
#        print self, items
        widget = self.get_widget()
        widget.clear()
        for item in items:
            widget.addItem(item)

    def set_multiselect(self, multiselect, widget=None):
        """
        """
        widget = self.get_widget()
        if multiselect:
            mode = QAbstractItemView.ExtendedSelection
        else:
            mode = QAbstractItemView.SingleSelection

        widget.setSelectionMode(mode)

    #--------------------------------------------------------------------------
    # Observers
    #--------------------------------------------------------------------------
    @observe('items', 'multiselect', 'operations')
    def _update_proxy(self, change):
        """ An observer which sends state change to the proxy.

        """
        # The superclass handler implementation is sufficient.
        name = change['name']
        if self.get_widget():
            if name == 'items':
                self.set_items(change['value'])
            elif name == 'multiselect':
                self.set_multi_select(self.multiselect)

    def clear_selection(self):
        widget = self.get_widget()
        for i in range(widget.count()):
            item = widget.item(i)
            widget.setItemSelected(item, False)

    def refresh_items(self):
        widget = self.get_widget()
        widget.clear()
        for item in self.items:
            widget.addItem(item)
