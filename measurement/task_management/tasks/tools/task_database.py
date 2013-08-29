# -*- coding: utf-8 -*-
"""
"""
from traits.api import HasTraits, Dict, Bool, Any
from threading import Lock

class TaskDatabase(HasTraits):
    """
    """
    _running = Bool(False)
    _database = Dict()
    _lock = Any

    def set_value(self, node_path, value_name, value):
        """Method used to set the value of the entry at the specified path

        Parameters:
        ----------
        node_path : str
            Path to the node holding the value to be set

        value_name : str
            Public key associated with the value to be set, internally converted
            so that we do not mix value and nodes

        value : any
            Actual value to be stored

        Returns
        -------
        new_val : bool
            Boolean indicating whether or not a new entry has been created in
            the database
        """
        node = self._go_to_path(node_path)
        safe_value_name = '_' + value_name
        new_val = False
        if not node.has_key(safe_value_name):
            new_val = True

        if self._running:
            self._lock.acquire()
            node[safe_value_name] = value
            self._lock.release()
        else:
            node[safe_value_name] = value

        return new_val

    def get_value(self, assumed_path, value_name):
        """Method to get a value from the database from its name and a path

        This method returns the value stored under the specified name. It starts
        looking at the specified path and if necessary goes up in the hierarchy.

        Parameters
        ----------
        assumed_path : str
            Path where we start looking for the entry

        value_name : str
            Name of the value we are looking for

        Returns
        -------
        value : any
            Value stored under the entry value_name
        """
        assumed_node = self._go_to_path(assumed_path)
        safe_value_name = '_' + value_name

        if assumed_node.has_key(safe_value_name):
            if self._running:
                self._lock.acquire()
                value = assumed_node[safe_value_name]
                self._lock.release()
            else:
                value = assumed_node[safe_value_name]
            return value

        else:
            new_assumed_path = assumed_path.rpartition('/')[0]
            return self.get_value(new_assumed_path, value_name)

    def delete_value(self, node_path, value_name):
        """Method to remove an entry from the specified node

        This method remove the specified entry from the specified node. This
        method is thread safe even if it shouldn't be used once the setup of the
        task is done.

        Parameters
        ----------
        assumed_path : str
            Path where we start looking for the entry

        value_name : str
            Name of the value we are looking for
        """
        node = self._go_to_path(node_path)
        safe_value_name = '_' + value_name

        if node.has_key(safe_value_name):
            if self._running:
                self._lock.acquire()
                del node[safe_value_name]
                self._lock.release()
            else:
                del node[safe_value_name]
        else:
            err_str = 'No entry {} in node {}'.format(value_name, node_path)
            raise ValueError(err_str)

    def list_accessible_entries(self, node_path):
        """Method used to get a list of all entries accessible from a node

        Parameters:
        ----------
        node_path : str
            Path to the node parent of the new one

        Returns
        -------
        entries_list : list
            List of entries accessible from the specified node
        """
        entries = []
        while node_path is not 'root':
            node = self._go_to_path(node_path)
            keys = node.keys()
            for key in keys:
                if not isinstance(node[key], dict):
                    entries.append(key)
            node_path = node_path.rpartition('/')[0]

        node = self._go_to_path(node_path)
        keys = node.keys()
        for key in keys:
            if not isinstance(node[key], dict):
                entries.append(key)

        return entries

    def create_node(self, parent_path, node_name):
        """Method used to create a new node in the database

        This method creates a new node in the database at the specified path.
        This method is not thread safe safe as the hierarchy of the tasks'
        database is not supposed to change during a measurement but only during
        the configuration phase

        Parameters:
        ----------
        parent_path : str
            Path to the node parent of the new one

        node_name : str
            Name of the new node to create
        """
        parent_node = self._go_to_path(parent_path)
        parent_node[node_name] = {}

    def rename_node(self, parent_path, new_name, old_name):
        """Method used to rename a node in the database

        This method renames the node at the specified path.
        This method is not thread safe safe as the hierarchy of the tasks'
        database is not supposed to change during a measurement but only during
        the configuration phase

        Parameters:
        ----------
        node_path : str
            Path to the node being renamed

        node_name : str
            New name of node
        """
        parent_node = self._go_to_path(parent_path)
        parent_node[new_name] = parent_node[old_name]
        del parent_node[old_name]

    def delete_node(self, parent_path, node_name):
        """Method used to an existing node from the database

        This method deltes a node in the database at the specified path.
        This method is not thread safe safe as the hierarchy of the tasks'
        database is not supposed to change during a measurement but only during
        the configuration phase

        Parameters:
        ----------
        parent_path : str
            Path to the node parent of the new one

        node_name : str
            Name of the new node to create
        """
        parent_node = self._go_to_path(parent_path)
        if node_name in parent_node:
            del parent_node[node_name]
        else:
            err_str = 'No node {} at the path {}'.format(node_name, parent_path)
            raise ValueError(err_str)

    def prepare_for_running(self):
        """
        """
        self._lock = Lock()
        self._running = True

    def _go_to_path(self, path):
        """Method used to reach a node specified by a path
        """
        node = self._database
        if path == 'root':
            return node

        #Decompose the path in database keys
        keys = path.split('/')
        #Remove first key (ie 'root' as we are not trying to access it)
        del keys[0]

        for key in keys:
            if key in node:
                node = node[key]
            else:
                ind = keys.index(key)
                if ind == 0:
                    err_str = 'Path {} is invalid, no key {} in root'.format(
                                path, key)
                else:
                    err_str = 'Path {} is invalid, no key {} in node {}'.format(
                                path, key, keys[ind-1])
                raise ValueError(err_str)

        return node
