# -*- coding: utf-8 -*-
#==============================================================================
# module : base_engine.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================

from atom.api import Atom, Event, Callable
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

    def prepare_to_run(self, root, monitored_entries):
        """
        """
        mes = cleandoc('''''')
        raise NotImplementedError(mes)

    def run(self):
        """
        """
        mes = cleandoc('''''')
        raise NotImplementedError(mes)

    def stop(self):
        """
        """
        mes = cleandoc('''''')
        raise NotImplementedError(mes)

    def exit(self):
        """
        """
        mes = cleandoc('''''')
        raise NotImplementedError(mes)

    def force_stop(self):
        """
        """
        mes = cleandoc('''''')
        raise NotImplementedError(mes)

    def force_exit(self):
        """
        """
        mes = cleandoc('''''')
        raise NotImplementedError(mes)


class Engine(Declarative):
    """
    """

    # Factory function returning an instance of the engine.
    factory = d_(Callable())
