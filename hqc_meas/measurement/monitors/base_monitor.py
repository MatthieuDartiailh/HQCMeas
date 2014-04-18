# -*- coding: utf-8 -*-
#==============================================================================
# module : base_monitor.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================

from atom.api import Callable, List, Str, Bool, Unicode, ForwardTyped
from enaml.core.declarative import Declarative, d_
from inspect import cleandoc

from hqc_meas.utils.atom_util import HasPrefAtom


class BaseMonitor(HasPrefAtom):
    """ Base class for all monitors.

    """
    # Declaration defining this editor.
    declaration = ForwardTyped(lambda: Monitor)

    # Name of the monitored measure.
    measure_name = Str().tag(pref=True)

    # Status of the current measure.
    measure_status = Str()

    # List of database which should be observed
    database_entries = List(Str())

    # Whether or not to show the monitor on start-up
    auto_show = Bool(True).tag(pref=True)

    def start(self, parent_ui):
        """ Start the activity of the monitor.

        It is the reponsability of the monitor to display any widget,
        the provided widget can be used as parent. The auto-show member value
        should be respected.

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
        the measure is started. The value received will be a tuple containing
        the name of the updated database entry and its new value.

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

    def clear_state(self):
        """ Clear the monitor state.

        """
        pass

    def get_state(self):
        """ Get all necessary informations to rebuild the monitor.

        Returns
        -------
        state : dict(str: str or dict)
            Dict containing all the necessary information to rebuild the
            monitor.

        """
        return self.preferences_from_members()

    def set_state(self, state):
        """ Use dict to restore the monitor state.

        Returns
        -------
        state : dict(str: str or dict)
            Dict containing all the necessary information to rebuild the
            monitor.

        """
        self.update_members_from_preferences(**state)

    def get_editor_page(self):
        """ Access the notebook page which can be used to edit the monitor.

        Returns
        -------
        page : enaml.widgets.Page
            Notebook page which can be used to edit the monitor.

        """
        mess = cleandoc('''This method should be implemented by subclasses of
                        BaseMonitor''')
        raise NotImplementedError(mess)

    def show_monitor(self, parent_ui):
        """ Show the monitor if pertinent using the provided parent.

        By default this is a no-op assuming the monitor has no ui. If a ui is
        already active it should be a no-op or restore the monitor.

        Parameters
        ----------
        parent_ui : enaml.widgets.Widget
            Parent to use for the display.

        """
        pass


class Monitor(Declarative):
    """ Extension for the 'monitors' extension point of a MeasurePlugin.

    The name member inherited from Object should always be set to an easily
    understandable name for the user.

    """
    # Id of the monitor, this can be different from the id of the plugin
    # declaring it but does not have to.
    id = d_(Unicode())

    # Description of the monitor.
    description = d_(Unicode())

    # Factory function returning an instance of the monitor. This callable
    # should take as arguments the workbench, the monitor declaration and the
    # optionnal keyword raw signaling whether or not to initialize the monitor
    # with default values (False by default).
    factory = d_(Callable())
