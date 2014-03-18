# -*- coding: utf-8 -*-
#==============================================================================
# module : workspace.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
import logging
import os
import enaml
from atom.api import Instance, Typed
from enaml.workbench.ui.api import Workspace
from inspect import cleandoc
from collections import defaultdict

from .measure import Measure
from .engines.base_engine import BaseEngine
from .plugin import MeasurePlugin

with enaml.imports():
    from .checks_display import ChecksDisplay


def extract_runtimes(walk, runtimes):
    """ Extract the runtime dependencies of a measurement from a walk.

    Parameters
    ----------
    walk : dict
        The nested dictionary returned by the walk method of the root task.

    runtimes : list(str)
        The list of runtime dependencies to look for.

    Returns
    -------
    results : dict(str: set)
        Dict containing the runtimes dependencies as sets. This dict can then
        be used to gather function and or classes needed at runtime.

    """
    results = defaultdict(set)
    for step in walk:
        if isinstance(step, list):
            aux = extract_runtimes(step)
            for key in aux:
                results[key].update(aux[key])
        else:
            for runtime in runtimes:
                if runtime in step:
                    results[runtime].add(step[runtime])

    return results


class MeasureSpace(Workspace):

    _plugin = Typed(MeasurePlugin)
    _engine = Instance(BaseEngine)
    _running_measure = Typed(Measure)

    def start(self):
        """
        """
        pass

    def stop(self):
        """
        """
        pass

    def enqueue_measure(self, measure):
        """Put a measure in the queue if it pass the tests.

        First the check method of the measure is called. If the tests pass,
        the measure is enqueued and finally saved in the default folder
        ('default_path' attribute of the `RootTask` describing the measure).
        Otherwise the list of the failed tests is displayed to the user.

        Parameters
        ----------
        measure : instance(`Measure`)
            Instance of `Measure` representing the measure.

        Returns
        -------
        bool :
            True is the measure was successfully enqueued, False otherwise.

        """
        logger = logging.getLogger(__name__)

        # First of all build the runtime dependencies
        walk = measure.root_task.walk(['selected_driver', 'selected_profile'])
        res = extract_runtimes(walk, ['selected_driver',
                                      'selected_profile'])
        drivs = res['selected_driver']
        profs = res['selected_profile']

        core = self.workbench.get_plugin('enaml.workbench.core')
        com = u'hqc_meas.instr_manager.drivers_request'
        res, drivers = core.invoke_command(com, {'drivers': list(drivs)}, self)
        if not res:
            mes = cleandoc('''Failed to get all drivers for the measure,
                           missing :{}'''.format(drivers))
            logger.info(mes)
            return False

        com = u'hqc_meas.instr_manager.profiles_request'
        res, profiles = core.invoke_command(com, {'profiles': list(profs)},
                                            self._plugin)
        if not res and profiles:
            mes = cleandoc('''Failed to get all profiles for the measure,
                           missing :{}'''.format(profiles))
            logger.info(mes)
            return False

        test_instr = res
        if not test_instr and not profiles:
            mes = cleandoc('''The profiles requested for the measurement {} are
                           not available, instr tests will be skipped and
                           performed before actually starting the
                           measure.'''.format(measure.name))
            logger.info(mes)

        measure.root_task.run_time = {'drivers': drivers,
                                      'profiles': profiles}

        check, errors = measure.run_checks(self.workbench,
                                           test_instr=test_instr)

        core.invoke_command(u'hqc_meas.instr_manager.profiles_released',
                            {'profiles': profiles}, self._plugin)

        if check:
            default_filename = measure.monitor.measure_name + '_last_run.ini'
            path = os.path.join(measure.root_task.default_path,
                                default_filename)
            measure.save_measure(path)
            meas = Measure.load_measure(self.workbench, path)
            # Here don't keep the profiles in the runtime as it will defeat the
            # purpose of the manager.
            meas.root_task.run_time = {'drivers': drivers}
            meas.store['profiles'] = profs
            self._plugin.enqueued_measures.append(meas)

            return True

        else:
            ChecksDisplay(errors=errors).exec_()
            return False

    def start_processing_measures(self):
        """ Starts to perform the measurement in the queue.

        Measure will be processed in their order of appearance in the queue.

        """
        # Here reset all flags concerning stopping, etc.
        # TODO xx

        measure = self._find_next_measure()
        if measure is not None:
            self._start_measure()

    def process_single_measure(self, index=0):
        """ Performs a single measurement and then stops.

        Parameters
        ----------
        index : int
            Index of the measurement to perform in the queue.

        """
        # Reset flags and set stop flags to perform a single measure.
        # TODO v

        try:
            measure = self._plugin.enqueued_measures[index]
        except IndexError:
            logger = logging.getLogger(__name__)
            mes = 'Tried to start a measure not currently in the queue'
            logger.info(mes)
            measure = None

        if measure is not None:
            self._start_measure(measure)

    def stop_current_measure(self):
        """
        """
        self._engine.stop()

    def stop_processing_measures(self):
        """
        """
        self._engine.exit()

    def force_stop_measure(self):
        """
        """
        pass

    def force_stop_processing(self):
        """
        """
        pass

    def listen_to_engine(self, change):
        """ Observer for the 'done' event of the engine

        """
        pass

    def _start_measure(self, measure):
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
            # TODO here call the function listening the engine to try to run
            # the next measure if there is one.

        measure.root_task.run_time.update({'profiles': profiles})

        # Collect headers.
        measure.collect_headers(self.workbench)

        # Start the engine if it has not already been done.

        # Call engine prepare to run method.

        # Discard old monitors if there is any remaining.

        # Start new monitors, connect them and show.

        # Connect signal handlers to engine.

        # Ask the engine to start the measure.

    def _find_next_measure(self):
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
            if measure.status == 'EDITING':
                i += 1
                measure = None
            else:
                break

        return measure
