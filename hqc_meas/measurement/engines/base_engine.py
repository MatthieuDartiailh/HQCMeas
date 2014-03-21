# -*- coding: utf-8 -*-
#==============================================================================
# module : base_engine.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================

from atom.api import Atom, Event, Callable, Bool
from enaml.core.declarative import Declarative, d_
from inspect import cleandoc


class BaseEngine(Atom):
    """ Base class for all engines.

    An engine is responsible for performing a measurement given a hierarchical
    ensemble of tasks.

    """

    # Event used to pass news about the measurement progress.
    news = Event()

    # Event through the engine signals it is done with a measure.
    done = Event()

    # Bool representing the current state of the engine.
    active = Bool()

    def prepare_to_run(self, root, monitored_entries):
        """ Make the engine ready to perform a measure.

        This method does not start the engine.

        Parameters
        ----------
        root : RootTask
            The root task representing the measure to perform.

        monitored : iterable
            The database entries to observe. Any change of one of these entries
            will be notified by the news event.

        """
        mes = cleandoc('''''')
        raise NotImplementedError(mes)

    def run(self):
        """ Start the execution of the measure by the engine.

        """
        mes = cleandoc('''''')
        raise NotImplementedError(mes)

    def stop(self):
        """ Ask the engine to stop the current measure.

        This method should not wait for the engine to stop.

        """
        mes = cleandoc('''''')
        raise NotImplementedError(mes)

    def exit(self):
        """ Ask the engine top stop completely.

        After a call to this method the engine may need to re-initialize a
        number of things before running the next measure. This method should
        not wait for the engine to exit.

        """
        mes = cleandoc('''''')
        raise NotImplementedError(mes)

    def force_stop(self):
        """ Force the engine to stop the current measure.

        This method should stop the process no matter what is going on. It can
        block.

        """
        mes = cleandoc('''''')
        raise NotImplementedError(mes)

    def force_exit(self):
        """ Force the engine to exit.

        This method should stop the process no matter what is going on. It can
        block.

        """
        mes = cleandoc('''''')
        raise NotImplementedError(mes)


class Engine(Declarative):
    """ Extension for the 'engines' extension point of a MeasurePlugin.

    """

    # Factory function returning an instance of the engine.
    factory = d_(Callable())