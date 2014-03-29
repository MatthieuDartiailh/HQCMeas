# -*- coding: utf-8 -*-
#==============================================================================
# module : base_monitor.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================

from atom.api import Event, Callable, Bool, List, Str
from enaml.core.declarative import Declarative, d_
from inspect import cleandoc

from hqc_meas.utils.atom_util import PrefAtom


class BaseMonitor(PrefAtom):
    """ Base class for all monitors.

    """

    # Name of the monitored measure.
    measure_name = Str().tag(pref=True)

    # List of database which should be observed
    database_entries = List(Str())

    def start(self, parent_ui):
        """ Start the activity of the monitor.

        It is the reponsability of the monitor to display any widget,
        the provided widget can be used as parent.

        Parameters
        ----------
        parent_ui : Widget
            Enaml widget to use as a parent for any ui to be shown.

        """
        mess = cleandoc('''This method should be implemented by subclasses of
                        BaseMonitor''')
        raise NotImplementedError(mess)

    def stop(self):
        """ Stop the activity of the monitor.

        If the monitor opened any window it is responsability to close them at
        this point.

        """
        mess = cleandoc('''This method should be implemented by subclasses of
                        BaseMonitor''')
        raise NotImplementedError(mess)

    def refresh_monitored_entries(self, entries=[]):
        """ Refresh all the entries of the monitor.

        Parameters
        ----------
        entries : list(str), optionnal
            List of the database entries to consider, if empty the already
            known entries will be used.

        """
        mess = cleandoc('''This method should be implemented by subclasses of
                        BaseMonitor''')
        raise NotImplementedError(mess)

    def process_news(self, change):
        """ Handle news received from the engine.

        This method should be connected to the news event of the engine when
        the measure is started.

        """
        mess = cleandoc('''This method should be implemented by subclasses of
                        BaseMonitor''')
        raise NotImplementedError(mess)

    def database_modified(self, change):
        """ Handle the database of the root task of the measure being modified.

        This method should be connected to the notifier of the database of the
        root task of the measure during edition.

        """
        mess = cleandoc('''This method should be implemented by subclasses of
                        BaseMonitor''')
        raise NotImplementedError(mess)

    def get_state(self):
        """ Get all necessary informations to rebuild the monitor.

        Returns
        -------
        state : dict(str: str or dict)
            Dict containing all the necessary information to rebuild the
            monitor.

        """
        mess = cleandoc('''This method should be implemented by subclasses of
                        BaseMonitor''')
        raise NotImplementedError(mess)

    def set_state(self, state):
        """ Use dict to restore the monitor state.

        Returns
        -------
        state : dict(str: str or dict)
            Dict containing all the necessary information to rebuild the
            monitor.

        """
        mess = cleandoc('''This method should be implemented by subclasses of
                        BaseMonitor''')
        raise NotImplementedError(mess)


class Monitor(Declarative):
    """ Extension for the 'monitors' extension point of a MeasurePlugin.

    """

    # Factory function returning an instance of the monitor.
    factory = d_(Callable())
