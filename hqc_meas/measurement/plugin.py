# -*- coding: utf-8 -*-
#==============================================================================
# module : measure_plugin.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
import logging
from inspect import cleandoc
from atom.api import Typed, Unicode, Callable, Dict, ContainerList

from hqc_meas.utils.has_pref_plugin import HasPrefPlugin
from .engines.base_engine import BaseEngine
from .measure import Measure


INVALID_MEASURE_STATUS = ['EDITING', 'SKIPPED']


class MeasurePlugin(HasPrefPlugin):
    """
    """
    # Have to be here otherwise lose tons of infos when closing workspace

    # Currently edited measure.
    edited_measure = Typed(Measure)

    # Currently enqueued measures.
    enqueued_measures = ContainerList(Typed(Measure))

    # Currently run measure or last measure run.
    running_measure = Typed(Measure)

    engines = Dict(Unicode(), Callable())
    selected_engine = Unicode().tag(pref=True)
    engine_instance = Typed(BaseEngine)

#    monitors
#    default_monitors
#
#    checks
#    default_checks
#
#    headers
#    default_headers

    flags = Dict()

    def start_measure(self, measure):
        """ Start a new measure.

        """
        logger = logging.getLogger(__name__)

        # Requesting profiles.
        profiles = measure.store('profiles')
        core = self.workbench.get_plugin('enaml.workbench.core')

        com = u'hqc_meas.instr_manager.profiles_request'
        res, profiles = core.invoke_command(com, {'profiles': list(profiles)},
                                            self._plugin)
        if not res:
            mes = cleandoc('''The profiles requested for the measurement {} are
                           not available, the measurement cannot be performed
                           '''.format(measure.name))
            logger.info(mes)
            measure.status = 'SKIPPED'
            measure.infos = 'Skipped : failed to get requested profiles'
            # TODO here call the function listening the engine to try to run
            # the next measure if there is one.

        measure.root_task.run_time.update({'profiles': profiles})

        # Collect headers.
        measure.collect_headers(self.workbench)

        # Start the engine if it has not already been done.
        if not self.engine_instance:
            maker = self.engines[self.selected_engine]
            self.engine_instance = maker(self.workbench)

        engine = self.engine_instance

        # Call engine prepare to run method.
        entries = measure.collect_entries_to_observe()
        engine.prepare_to_run(measure.root_task, entries)

        # Discard old monitors if there is any remaining.
        for monitor in self.running_measure.monitors:
            monitor.shutdown()

        self.running_measure = measure
        measure.status = 'RUNNING'

        # Connect new monitors, and start them.
        for monitor in measure.monitors:
            engine.observe('news', monitor.process_news)
            monitor.start()

        # Connect signal handlers to engine.
        engine.observe('done', self.listen_to_engine)

        # Ask the engine to start the measure.
        engine.start()

    def listen_to_engine(self, change):
        """ Observer for the engine notifications.

        """
        pass

    def find_next_measure(self):
        """ Find the next runnable measure in the queue.

        Returns
        -------
        measure : Measure
            First valid measurement in the queue (ie not being edited), or None
            if there is no available measure.

        """
        enqueued_measures = self._plugin.enqueued_measures
        i = 0
        measure = None
        # Look for a measure not being currently edited. (Can happen if the
        # user is editing the second measure when the first measure ends).
        while i < len(enqueued_measures):
            measure = enqueued_measures[i]
            if measure.status in INVALID_MEASURE_STATUS:
                i += 1
                measure = None
            else:
                break

        return measure
