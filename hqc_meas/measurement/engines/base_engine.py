# -*- coding: utf-8 -*-
#==============================================================================
# module : base_engine.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================

from atom.api import Atom, Event, Callable, Bool, Unicode, ForwardTyped
from enaml.core.declarative import Declarative, d_
from inspect import cleandoc


class BaseEngine(Atom):
    """ Base class for all engines.

    An engine is responsible for performing a measurement given a hierarchical
    ensemble of tasks.

    """
    # Declaration defining this engine.
    declaration = ForwardTyped(lambda: Engine)

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

        monitored_entries : iterable
            The database entries to observe. Any change of one of these entries
            will be notified by the news event.

        """
        mes = cleandoc('''''')
        raise NotImplementedError(mes)

    def run(self):
        """ Start the execution of the measure by the engine.

        This method must not wait for the measure to complete to return.

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

    The name member inherited from Object should always be set to an easily
    understandable name for the user.

    """
    # Id of the engine, this can be different from the id of the plugin
    # declaring it but does not have to.
    id = d_(Unicode())

    # Description of the engine
    description = d_(Unicode())

    # Factory function returning an instance of the engine. This callable
    # should take as arguments the engine declaration and the workbench.
    factory = d_(Callable())

    # Callable called by the framework when this engine is selected. The
    # callable should take two arguments : the engine declaration. and
    # the workbench
    post_selection = d_(Callable(lambda declaration, workbench: None))

    # Callable called by the framework when the engine is deselected. The
    # callable should take two arguments : the engine declaration. and
    # the workbench
    post_deselection = d_(Callable(lambda declaration, workbench: None))

    # Callable called by the framework when the workspace is active and the
    # engine selected. The callable should take two arguments : the engine
    # declaration and the workspace.
    contribute_workspace = d_(Callable(lambda declaration, workspace: None))

    # Callable called by the framework when the workspace is active and the
    # engine deselected. The callable should take  two arguments : the engine
    # declaration and the workspace.
    remove_contribution = d_(Callable(lambda declaration, workspace: None))
