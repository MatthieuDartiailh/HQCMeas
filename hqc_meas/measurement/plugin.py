# -*- coding: utf-8 -*-
#==============================================================================
# module : measure_plugin.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
import logging
from inspect import cleandoc
from atom.api import Typed, Unicode, Dict, ContainerList
from time import sleep

from hqc_meas.utils.has_pref_plugin import HasPrefPlugin
from .engines.base_engine import BaseEngine, Engine
from .measure import Measure


INVALID_MEASURE_STATUS = ['EDITING', 'SKIPPED', 'FAILED', 'COMPLETED',
                          'INTERRUPTED']


# TODO handle extensions points
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

    # Dict holding the contributed Engine declarations.
    engines = Dict(Unicode(), Engine())

    # Currently selected engine represented by its manifest id.
    selected_engine = Unicode().tag(pref=True)

    # Instance of the currently used engine.
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

        # Discard old monitors if there is any remaining.
        for monitor in self.running_measure.monitors:
            monitor.shutdown()

        self.running_measure = measure

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

            # Simulate a message coming from the engine.
            done = {'value': ('SKIPPED', 'Failed to get requested profiles')}
            self._listen_to_engine(done)

        measure.root_task.run_time.update({'profiles': profiles})

        # Collect headers.
        measure.collect_headers(self.workbench)

        # Start the engine if it has not already been done.
        if not self.engine_instance:
            maker = self.engines[self.selected_engine]
            self.engine_instance = maker(self.workbench)

            # Connect signal handler to engine.
            self.engine_instance.observe('done', self._listen_to_engine)

        engine = self.engine_instance

        # Call engine prepare to run method.
        entries = measure.collect_entries_to_observe()
        engine.prepare_to_run(measure.root_task, entries)

        measure.status = 'RUNNING'
        measure.infos = 'The measure is running'

        # Connect new monitors, and start them.
        for monitor in measure.monitors:
            engine.observe('news', monitor.process_news)
            monitor.start()

        # Ask the engine to start the measure.
        engine.run()

    def stop_measure(self):
        """ Stop the currently active measure.

        """
        self.engine_instance.stop()

    def stop_processing(self):
        """ Stop processing the enqueued measure.

        """
        self.flags['stop_processing'] = True
        self.engine_instance.exit()

    def force_stop_measure(self):
        """ Force the engine to stop performing the current measure.

        """
        self.engine_instance.force_stop()

    def force_stop_processing(self):
        """ Force the engine to exit and stop processing measures.

        """
        self.flags['stop_processing'] = True
        self.engine_instance.force_exit()

    def find_next_measure(self):
        """ Find the next runnable measure in the queue.

        Returns
        -------
        measure : Measure
            First valid measurement in the queue or None if there is no
            available measure.

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

    def _listen_to_engine(self, change):
        """ Observer for the engine notifications.

        """
        status, infos = change['value']
        self.running_measure.status = status
        self.running_measure.infos = infos

        # Disconnect monitors.
        self.engine_instance.unobserve('news')

        # If we are supposed to stop, stop.
        if 'stop_processing' in self.flags:
            self.stop_processing()
            while not self.engine_instance.active:
                sleep(0.5)

        # Otherwise find the next measure, if there is none stop the engine.
        else:
            meas = self.find_next_measure()
            if meas is not None:
                self.start_measure(meas)
            else:
                self.stop_processing()
                while not self.engine_instance.active:
                    sleep(0.5)
