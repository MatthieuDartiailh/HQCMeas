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

from .measure import Measure
from .engines.base_engine import BaseEngine
from .plugin import MeasurePlugin

from ..tasks.tools.walks import flatten_walk

with enaml.imports():
    from .checks_display import ChecksDisplay


class MeasureSpace(Workspace):

    _plugin = Typed(MeasurePlugin)

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
        res = flatten_walk(walk, ['selected_driver',
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

        measure = self._plugin.find_next_measure()
        if measure is not None:
            self._plugin.start_measure()

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
            self._plugin.start_measure(measure)

    def stop_current_measure(self):
        """
        """
        # TODO call plugin method

    def stop_processing_measures(self):
        """
        """
        # TODO call plugin method

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
