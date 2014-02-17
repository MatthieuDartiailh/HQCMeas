# -*- coding: utf-8 -*-
"""
Created on Tue Nov 05 11:57:33 2013

@author: hqc
"""
from atom.api import (Atom, Unicode, Bool, List, Value, Property, ContainerList,
                  Dict, Typed, Instance, Str)
                  
#from enaml.qt.deferred_caller import deferredCall
from enaml.widgets.api import Menu

class TreeNode (Atom):
    """ Represents a tree node. Used by the tree editor and tree editor factory
        classes.
    """

    #---------------------------------------------------------------------------
    #  Trait definitions:
    #---------------------------------------------------------------------------

    # Name of trait containing children (if '', the node is a leaf).
    children = Str()

    # Either the name of a trait containing a label, or a constant label, if
    # the string starts with '='.
    label = Unicode()

    # The name of a trait containing a list of labels for any columns.
    column_labels = Unicode()

    # Either the name of a trait containing a tooltip, or constant tooltip, if
    # the string starts with '='.
    tooltip = Unicode()

    # Name to use for a new instance
    name = Unicode()

    # Can the object's children be renamed?
    rename = Bool( True )

    # Can the object be renamed?
    rename_me = Bool( True )

    # Can the object's children be copied?
    copy = Bool( True )

    # Can the object's children be deleted?
    delete = Bool( True )

    # Can the object be deleted (if its parent allows it)?
    delete_me = Bool( True )

    # Can children be inserted (vs. appended)?
    insert = Bool( True )

    # Should tree nodes be automatically opened (expanded)?
    auto_open = Bool( False )

    # Automatically close sibling tree nodes?
    auto_close = Bool( False )

    # List of object classes than can be added or copied
    add = List(Value())

    # List of object classes that can be moved
    move = List(Value())

    # List of object classes and/or interfaces that the node applies to
    node_for = List(Value())

    # Tuple of object classes that the node applies to
    node_for_class = Property()

    # List of object interfaces that the node applies to
    node_for_interface = Property()

    # Right-click context menu. The value can be one of:
    menu = Instance(Menu)

    # Name of leaf item icon
    icon_item = Unicode( '<item>' )

    # Name of group item icon
    icon_group = Unicode( '<group>' )

    # Name of opened group item icon
    icon_open = Unicode( '<open>' )

    # Resource path used to locate the node icon
    icon_path = Unicode

    # Selector or name for background color
    background = Value('white')

    # Selector or name for foreground color
    foreground = Value('black')
    
    _py_data = Value()

    #---------------------------------------------------------------------------
    #  Initializes the object:
    #---------------------------------------------------------------------------

    def __init__ ( self, **kwargs ):
        super( TreeNode, self ).__init__( **kwargs )
        if self.icon_path == '':
            self.icon_path = 'Icon'

    #-- Property Implementations -----------------------------------------------

    @node_for_class.getter
    def _get_node_for_class ( self ):
        return tuple([klass for klass in self.node_for])

    #-- Overridable Methods: ---------------------------------------------------

    #---------------------------------------------------------------------------
    #  Returns whether chidren of this object are allowed or not:
    #---------------------------------------------------------------------------

    def allows_children ( self, obj ):
        """ Returns whether this object can have children.
        """
        return (self.children != '')

    #---------------------------------------------------------------------------
    #  Returns whether or not the object has children:
    #---------------------------------------------------------------------------

    def has_children ( self, obj ):
        """ Returns whether the object has children.
        """
        return (len( self.get_children( obj ) ) > 0)

    #---------------------------------------------------------------------------
    #  Gets the object's children:
    #---------------------------------------------------------------------------

    def get_children ( self, obj ):
        """ Gets the object's children.
        """
        return getattr( obj, self.children )

    #---------------------------------------------------------------------------
    #  Gets the object's children identifier:
    #---------------------------------------------------------------------------

    def get_children_id ( self, obj ):
        """ Gets the object's children identifier.
        """
        return self.children

    #---------------------------------------------------------------------------
    #  Appends a child to the object's children:
    #---------------------------------------------------------------------------

    def append_child ( self, obj, child ):
        """ Appends a child to the object's children.
        """
        getattr( obj, self.children ).append( child )

    #---------------------------------------------------------------------------
    #  Inserts a child into the object's children:
    #---------------------------------------------------------------------------

    def insert_child ( self, obj, index, child ):
        """ Inserts a child into the object's children.
        """
        getattr( obj, self.children )[ index: index ] = [ child ]

    #---------------------------------------------------------------------------
    #  Confirms that a specified object can be deleted or not:
    #  Result = True:  Delete object with no further prompting
    #         = False: Do not delete object
    #         = other: Take default action (may prompt user to confirm delete)
    #---------------------------------------------------------------------------

    def confirm_delete ( self, obj ):
        """ Checks whether a specified object can be deleted.

        Returns
        -------
        * **True** if the object should be deleted with no further prompting.
        * **False** if the object should not be deleted.
        * Anything else: Caller should take its default action (which might
          include prompting the user to confirm deletion).
        """
        return None

    #---------------------------------------------------------------------------
    #  Deletes a child at a specified index from the object's children:
    #---------------------------------------------------------------------------

    def delete_child ( self, obj, index ):
        """ Deletes a child at a specified index from the object's children.
        """
        print getattr(obj, self.children)
        del getattr( obj, self.children )[ index ]
        print getattr(obj, self.children)

    #---------------------------------------------------------------------------
    #  Sets up/Tears down a listener for 'children replaced' on a specified
    #  object:
    #---------------------------------------------------------------------------

#    def when_children_replaced ( self, obj, listener, remove ):
#        """ Sets up or removes a listener for children being replaced on a
#        specified object.
#        """
##        print 'toto', obj, listener, self.children
#        if remove:
#            obj.unobserve(str(self.children), listener)
#        else:
##        print getattr(obj, self.children)
#            obj.observe(str(self.children),  listener)
##        print obj.has_observers(self.children)
#
#    #---------------------------------------------------------------------------
#    #  Sets up/Tears down a listener for 'children changed' on a specified
#    #  object:
#    #---------------------------------------------------------------------------
#
#    def when_children_changed ( self, obj, listener, remove ):
#        """ Sets up or removes a listener for children being changed on a
#        specified object.
#        """
#        if remove:
#            obj.unobserve(str(self.children), listener)
#        else:
#            obj.observe(self.children,  listener)

    #---------------------------------------------------------------------------
    #  Gets the label to display for a specified object:
    #---------------------------------------------------------------------------

    def get_label (self, obj):
        """ Gets the label to display for a specified object.
        """
        label = self.label
        if label[:1] == '=':
            return label[1:]

        label = getattr(obj, label)

        return label

    #---------------------------------------------------------------------------
    #  Sets the label for a specified object:
    #---------------------------------------------------------------------------

    def set_label ( self, obj, label ):
        """ Sets the label for a specified object.
        """
        label_name = self.label
        if label_name[:1] != '=':
            setattr( obj, label_name, label )

    #---------------------------------------------------------------------------
    #  Sets up/Tears down a listener for 'label changed' on a specified object:
    #---------------------------------------------------------------------------

    def when_label_changed ( self, obj, listener, remove ):
        """ Sets up or removes a listener for the label being changed on a
        specified object.
        """
        label = self.label
        if label[:1] != '=':
            if remove:
                obj.unobserve(label, listener)
            else:
                obj.observe(label, listener)

    def get_column_labels(self, obj):
        """ Get the labels for any columns that have been defined.
        """
        trait = self.column_labels
        return []
        labels = getattr(obj, trait)
        if not labels:
            labels = []
        formatted = []
        for formatter, label in map(None, self.column_formatters, labels):
            # If the list of column formatters is shorter than the list of
            # labels, then map(None) will extend it with Nones. Just pass the label
            # as preformatted. Similarly, explicitly using None in the list will
            # pass through the item.
            if formatter is None:
                formatted.append(label)
            else:
                formatted.append(formatter(label))
        return formatted

    def when_column_labels_change(self, obj, listener, remove):
        """ Sets up or removes a listener for the column labels being changed on
        a specified object.

        This will fire when either the list is reassigned or when it is
        modified. I.e., it listens both to the trait change event and the
        trait_items change event. Implement the listener appropriately to handle
        either case.
        """
        trait = self.column_labels
        if trait != '':
            if remove:
                obj.unobserve(trait, listener)
            else:
                obj.observe(trait, listener)

    #---------------------------------------------------------------------------
    #  Gets the tooltip to display for a specified object:
    #---------------------------------------------------------------------------

    def get_tooltip ( self, obj ):
        """ Gets the tooltip to display for a specified object.
        """
        tooltip = self.tooltip
        if tooltip == '':
            return tooltip

        if tooltip[:1] == '=':
            return tooltip[1:]

        tooltip = getattr( obj, tooltip)
        if not tooltip:
            tooltip = ''

        if self.tooltip_formatter is None:
            return tooltip

        return self.tooltip_formatter( obj, tooltip )

    #---------------------------------------------------------------------------
    #  Returns the icon for a specified object:
    #---------------------------------------------------------------------------

    def get_icon ( self, obj, is_expanded ):
        """ Returns the icon for a specified object.
        """
        if not self.allows_children( obj ):
            return self.icon_item

        if is_expanded:
            return self.icon_open

        return self.icon_group

    #---------------------------------------------------------------------------
    #  Returns the path used to locate an object's icon:
    #---------------------------------------------------------------------------

    def get_icon_path (self, obj):
        """ Returns the path used to locate an object's icon.
        """
        return self.icon_path

    #---------------------------------------------------------------------------
    #  Returns the name to use when adding a new object instance (displayed in
    #  the 'New' submenu):
    #---------------------------------------------------------------------------

    def get_name (self, obj):
        """ Returns the name to use when adding a new object instance
            (displayed in the "New" submenu).
        """
        return self.name

    #---------------------------------------------------------------------------
    #  Returns the right-click context menu for an object:
    #---------------------------------------------------------------------------

    def get_menu ( self, context):
        """ Returns the right-click context menu for an object.
        """
        if self.menu:
            self.menu.context = context
            return self.menu
        else:
            return None

    def get_background(self, obj) :
        background = self.background
        if isinstance(background, basestring) :
            background = getattr(obj, background, background)
        return background

    def get_foreground(self, obj) :
        foreground = self.foreground
        if isinstance(foreground, basestring) :
            foreground = getattr(obj, foreground, foreground)
        return foreground

    #---------------------------------------------------------------------------
    #  Returns whether or not the object's children can be renamed:
    #---------------------------------------------------------------------------

    def can_rename ( self, obj ):
        """ Returns whether the object's children can be renamed.
        """
        return self.rename

    #---------------------------------------------------------------------------
    #  Returns whether or not the object can be renamed:
    #---------------------------------------------------------------------------

    def can_rename_me ( self, obj ):
        """ Returns whether the object can be renamed.
        """
        return self.rename_me

    #---------------------------------------------------------------------------
    #  Returns whether or not the object's children can be copied:
    #---------------------------------------------------------------------------

    def can_copy ( self, obj ):
        """ Returns whether the object's children can be copied.
        """
        return self.copy

    #---------------------------------------------------------------------------
    #  Returns whether or not the object's children can be deleted:
    #---------------------------------------------------------------------------

    def can_delete ( self, obj ):
        """ Returns whether the object's children can be deleted.
        """
        return self.delete

    #---------------------------------------------------------------------------
    #  Returns whether or not the object can be deleted:
    #---------------------------------------------------------------------------

    def can_delete_me ( self, obj ):
        """ Returns whether the object can be deleted.
        """
        return self.delete_me

    #---------------------------------------------------------------------------
    #  Returns whether or not the object's children can be inserted (or just
    #  appended):
    #---------------------------------------------------------------------------

    def can_insert ( self, obj ):
        """ Returns whether the object's children can be inserted (vs.
        appended).
        """
        return self.insert

    #---------------------------------------------------------------------------
    #  Returns whether or not the object's children should be auto-opened:
    #---------------------------------------------------------------------------

    def can_auto_open ( self, obj ):
        """ Returns whether the object's children should be automatically
        opened.
        """
        return self.auto_open

    #---------------------------------------------------------------------------
    #  Returns whether or not the object's children should be auto-closed:
    #---------------------------------------------------------------------------

    def can_auto_close ( self, obj ):
        """ Returns whether the object's children should be automatically
        closed.
        """
        return self.auto_close

    #---------------------------------------------------------------------------
    #  Returns whether or not this is the node that should handle a specified
    #  object:
    #---------------------------------------------------------------------------

    def is_node_for ( self, obj ):
        """ Returns whether this is the node that handles a specified object.
        """
        return (isinstance(obj, self.node_for_class))

    #---------------------------------------------------------------------------
    #  Returns whether a given 'add_object' can be added to an object:
    #---------------------------------------------------------------------------

    def can_add ( self, obj, add_object ):
        """ Returns whether a given object is droppable on the node.
        """
        klass = self._class_for( add_object )
        if self.is_addable( klass ):
            return True

        for item in self.move:
            if type( item ) in (List, ContainerList, Dict):
                item = item[0]
            if issubclass( klass, item ):
                return True

        return False

    #---------------------------------------------------------------------------
    #  Returns the list of classes that can be added to the object:
    #---------------------------------------------------------------------------

    def get_add ( self, obj ):
        """ Returns the list of classes that can be added to the object.
        """
        return self.add

    #---------------------------------------------------------------------------
    #  Returns the 'draggable' version of a specified object:
    #---------------------------------------------------------------------------

    def get_drag_object ( self, obj ):
        """ Returns a draggable version of a specified object.
        """
        return obj

    #---------------------------------------------------------------------------
    #  Returns a droppable version of a specified object:
    #---------------------------------------------------------------------------

    def drop_object ( self, obj, dropped_object ):
        """ Returns a droppable version of a specified object.
        """
        klass = self._class_for( dropped_object )
        if self.is_addable( klass ):
            return dropped_object

        for item in self.move:
            if type( item ) in (List, ContainerList, Dict):
                if issubclass( klass, item[0] ):
                    return item[1]( obj, dropped_object )
            elif issubclass( klass, item ):
                return dropped_object

        return dropped_object

    #---------------------------------------------------------------------------
    #  Handles an object being selected:
    #---------------------------------------------------------------------------

    def select ( self, obj ):
        """ Handles an object being selected.
        """
#        if self.on_select is not None:
#            self.on_select( obj )
#            return None

        return True

#    #---------------------------------------------------------------------------
#    #  Handles an object being clicked:
#    #---------------------------------------------------------------------------
#
#    def click ( self, obj ):
#        """ Handles an object being clicked.
#        """
#        if self.on_click is not None:
#            self.on_click( obj )
#            return None
#
#        return True
#
#    #---------------------------------------------------------------------------
#    #  Handles an object being double-clicked:
#    #---------------------------------------------------------------------------
#
#    def dclick ( self, obj):
#        """ Handles an object being double-clicked.
#        """
#        if self.on_dclick is not None:
#            self.on_dclick( obj)
#            return None
#
#        return True
#
#    #---------------------------------------------------------------------------
#    #  Handles an object being activated:
#    #---------------------------------------------------------------------------
#
#    def activated ( self, object ):
#        """ Handles an object being activated.
#        """
#        if self.on_activated is not None:
#            self.on_activated( object )
#            return None
#
#        return True

    #---------------------------------------------------------------------------
    #  Returns whether or not a specified object class can be added to the node:
    #---------------------------------------------------------------------------

    def is_addable ( self, klass ):
        """ Returns whether a specified object class can be added to the node.
        """
        for item in self.add:
            if type( item ) in (List, ContainerList, Dict):
                item = item[0]

            if issubclass( klass, item ):
                return True

        return False

    #---------------------------------------------------------------------------
    #  Returns the class of an object:
    #---------------------------------------------------------------------------

    def _class_for ( self, obj ):
        """ Returns the class of an object.
        """
        if isinstance( obj, type ):
            return obj

        return obj.__class__
        
#-------------------------------------------------------------------------------
#  'MultiTreeNode' object:
#-------------------------------------------------------------------------------

class MultiTreeNode ( TreeNode ):

    #---------------------------------------------------------------------------
    #  Trait definitions:
    #---------------------------------------------------------------------------

    # TreeNode that applies to the base object itself
    root_node = Typed(TreeNode)

    # List of TreeNodes (one for each sub-item list)
    nodes = List(Typed(TreeNode))

    #---------------------------------------------------------------------------
    #  Returns whether chidren of this object are allowed or not:
    #---------------------------------------------------------------------------

    def allows_children ( self, obj ):
        """ Returns whether this object can have children (True for this
        class).
        """
        return True

    #---------------------------------------------------------------------------
    #  Returns whether or not the object has children:
    #---------------------------------------------------------------------------

    def has_children ( self, obj ):
        """ Returns whether this object has children (True for this class).
        """
        return True

    #---------------------------------------------------------------------------
    #  Gets the object's children:
    #---------------------------------------------------------------------------

    def get_children ( self, obj ):
        """ Gets the object's children.
        """
        return [ ( obj, node ) for node in self.nodes ]

    #---------------------------------------------------------------------------
    #  Gets the object's children identifier:
    #---------------------------------------------------------------------------

    def get_children_id ( self, obj ):
        """ Gets the object's children identifier.
        """
        return ''

    #---------------------------------------------------------------------------
    #  Sets up/Tears down a listener for 'children replaced' on a specified
    #  object:
    #---------------------------------------------------------------------------

    def when_children_replaced ( self, obj, listener, remove ):
        """ Sets up or removes a listener for children being replaced on a
        specified object.
        """
        pass

    #---------------------------------------------------------------------------
    #  Sets up/Tears down a listener for 'children changed' on a specified
    #  object:
    #---------------------------------------------------------------------------

    def when_children_changed ( self, obj, listener, remove ):
        """ Sets up or removes a listener for children being changed on a
        specified object.
        """
        pass

    #---------------------------------------------------------------------------
    #  Gets the label to display for a specified object:
    #---------------------------------------------------------------------------

    def get_label ( self, obj ):
        """ Gets the label to display for a specified object.
        """
        return self.root_node.get_label( obj )

    #---------------------------------------------------------------------------
    #  Sets the label for a specified object:
    #---------------------------------------------------------------------------

    def set_label ( self, obj, label ):
        """ Sets the label for a specified object.
        """
        return self.root_node.set_label( obj, label )

    #---------------------------------------------------------------------------
    #  Sets up/Tears down a listener for 'label changed' on a specified object:
    #---------------------------------------------------------------------------

    def when_label_changed ( self, obj, listener, remove ):
        """ Sets up or removes a listener for the label being changed on a
        specified object.
        """
        return self.root_node.when_label_changed( obj, listener, remove )

    #---------------------------------------------------------------------------
    #  Returns the icon for a specified object:
    #---------------------------------------------------------------------------

    def get_icon ( self, obj, is_expanded ):
        """ Returns the icon for a specified object.
        """
        return self.root_node.get_icon( obj, is_expanded )

    #---------------------------------------------------------------------------
    #  Returns the path used to locate an object's icon:
    #---------------------------------------------------------------------------

    def get_icon_path ( self, obj ):
        """ Returns the path used to locate an object's icon.
        """
        return self.root_node.get_icon_path( obj )

    #---------------------------------------------------------------------------
    #  Returns the name to use when adding a new object instance (displayed in
    #  the 'New' submenu):
    #---------------------------------------------------------------------------

    def get_name ( self, obj ):
        """ Returns the name to use when adding a new object instance
            (displayed in the "New" submenu).
        """
        return self.root_node.get_name( obj )

    #---------------------------------------------------------------------------
    #  Gets the View to use when editing an object:
    #---------------------------------------------------------------------------

    def get_view ( self, obj ):
        """ Gets the view to use when editing an object.
        """
        return self.root_node.get_view( obj )

    #---------------------------------------------------------------------------
    #  Returns the right-click context menu for an object:
    #---------------------------------------------------------------------------

    def get_menu ( self, obj ):
        """ Returns the right-click context menu for an object.
        """
        return self.root_node.get_menu( obj )

    #---------------------------------------------------------------------------
    #  Returns whether or not the object's children can be renamed:
    #---------------------------------------------------------------------------

    def can_rename ( self, obj ):
        """ Returns whether the object's children can be renamed (False for
        this class).
        """
        return False

    #---------------------------------------------------------------------------
    #  Returns whether or not the object can be renamed:
    #---------------------------------------------------------------------------

    def can_rename_me ( self, obj ):
        """ Returns whether the object can be renamed (False for this class).
        """
        return False

    #---------------------------------------------------------------------------
    #  Returns whether or not the object's children can be copied:
    #---------------------------------------------------------------------------

    def can_copy ( self, obj ):
        """ Returns whether the object's children can be copied.
        """
        return self.root_node.can_copy( obj )

    #---------------------------------------------------------------------------
    #  Returns whether or not the object's children can be deleted:
    #---------------------------------------------------------------------------

    def can_delete ( self, obj ):
        """ Returns whether the object's children can be deleted (False for
        this class).
        """
        return False

    #---------------------------------------------------------------------------
    #  Returns whether or not the object can be deleted:
    #---------------------------------------------------------------------------

    def can_delete_me ( self, obj ):
        """ Returns whether the object can be deleted (True for this class).
        """
        return True

    #---------------------------------------------------------------------------
    #  Returns whether or not the object's children can be inserted (or just
    #  appended):
    #---------------------------------------------------------------------------

    def can_insert ( self, obj ):
        """ Returns whether the object's children can be inserted (False,
        meaning that children are appended, for this class).
        """
        return False

    #---------------------------------------------------------------------------
    #  Returns whether or not the object's children should be auto-opened:
    #---------------------------------------------------------------------------

    def can_auto_open ( self, obj ):
        """ Returns whether the object's children should be automatically
        opened.
        """
        return self.root_node.can_auto_open( obj )

    #---------------------------------------------------------------------------
    #  Returns whether or not the object's children should be auto-closed:
    #---------------------------------------------------------------------------

    def can_auto_close ( self, obj ):
        """ Returns whether the object's children should be automatically
        closed.
        """
        return self.root_node.can_auto_close( obj )

    #---------------------------------------------------------------------------
    #  Returns whether a given 'add_object' can be added to an object:
    #---------------------------------------------------------------------------

    def can_add ( self, obj, add_object ):
        """ Returns whether a given object is droppable on the node (False for
        this class).
        """
        return False

    #---------------------------------------------------------------------------
    #  Returns the list of classes that can be added to the object:
    #---------------------------------------------------------------------------

    def get_add ( self, obj ):
        """ Returns the list of classes that can be added to the object.
        """
        return []

    #-------------------------------------------------------------------------------
    #  Returns the 'draggable' version of a specified object:
    #-------------------------------------------------------------------------------

    def get_drag_object ( self, obj ):
        """ Returns a draggable version of a specified object.
        """
        return self.root_node.get_drag_object( obj )

    #---------------------------------------------------------------------------
    #  Returns a droppable version of a specified object:
    #---------------------------------------------------------------------------

    def drop_object ( self, obj, dropped_object ):
        """ Returns a droppable version of a specified object.
        """
        return self.root_node.drop_object( obj, dropped_object )

    #---------------------------------------------------------------------------
    #  Handles an object being selected:
    #---------------------------------------------------------------------------

    def select ( self, obj ):
        """ Handles an object being selected.
        """
        return self.root_node.select( obj )

    #---------------------------------------------------------------------------
    #  Handles an object being clicked:
    #---------------------------------------------------------------------------

#    def click ( self, object ):
#        """ Handles an object being clicked.
#        """
#        return self.root_node.click( object )
#
#    #---------------------------------------------------------------------------
#    #  Handles an object being double-clicked:
#    #---------------------------------------------------------------------------
#
#    def dclick ( self, object ):
#        """ Handles an object being double-clicked.
#        """
#        return self.root_node.dclick( object )
#
#    #---------------------------------------------------------------------------
#    #  Handles an object being activated:
#    #---------------------------------------------------------------------------
#
#    def activated ( self, object ):
#        """ Handles an object being activated.
#        """
#        return self.root_node.activated( object )