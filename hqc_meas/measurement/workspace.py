# -*- coding: utf-8 -*-
#==============================================================================
# module : workspace.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
import logging
import os
import enaml
from atom.api import Typed, Value
from enaml.workbench.ui.api import Workspace
from enaml.widgets.api import FileDialog
from inspect import cleandoc
from textwrap import fill

from .measure import Measure
from .plugin import MeasurePlugin

from ..tasks.tools.walks import flatten_walk

with enaml.imports():
    from enaml.stdlib.message_box import question
    from .checks.checks_display import ChecksDisplay
    from .engines.selection import EngineSelector
    from .content import MeasureContent


class MeasureSpace(Workspace):
    """
    """
    # Reference to the plugin to which the workspace is linked.
    plugin = Typed(MeasurePlugin)

    # Reference to the log panel model received from the log plugin.
    log_model = Value()

    def start(self):
        """
        """
        self.plugin = self.workbench.getplugin(u'hqc_meas.measure')
        self.plugin.workspace = self
        # TODO setup logging handler to redirect log to panel.
        self.content = MeasureContent(workspace=self)

    def stop(self):
        """
        """
        # TODO remove log handler
        self.plugin.workspace = None

    def new_measure(self):
        """
        """
        message = cleandoc("""The measurement you are editing is about to
                        be destroyed to create a new one. Press OK to
                        confirm, or Cancel to go back to editing and get a
                        chance to save it.""")

        result = question(self.content,
                          'Old measurement suppression',
                          fill(message.replace('\n', ' '), 79),
                          )
        if result is not None and result.action == 'accept':
            # TODO create brand new measure using defaults from plugin
            pass

    def save_measure(self, measure, mode):
        """ Save a measure in a file.

        Parameters
        ----------
        measure : Measure
            Measure to save.

        mode : str
            file: The user is asked to choose a file in which to save the
                measure.
            template: Save the whole measure as a template.

        """
        if mode == 'file':
            # TODO use new API
            full_path = FileDialog(parent=self.content,
                                   mode='save_file',
                                   filters=[u'*.ini']).exec_()
            if not full_path:
                return

            measure.save_measure(full_path)

        elif mode == 'template':
            message = cleandoc("""You are going to save the whole measurement
                                you are editing as a template. If you want to
                                save only a part of it, use the contextual
                                menu.""")

            result = question(self.content,
                              'Saving measurement',
                              fill(message.replace('\n', ' '), 79),
                              )

            if result is not None and result.action == 'accept':
                core = self.workbench.get_plugin(u'enaml.workbnch.core')
                cmd = u'hqc_meas.task_manager.save_task'
                core.invoke_command(cmd,
                                    {'task': measure.root_task,
                                     'mode': 'template'},
                                    self)

    def load_measure(self, mode):
        """ Load a measure.

        Parameters
        ----------
        mode : str
            file: ask the user to specify a file from which to load a measure.
            template: ask the user to choose a template and use default for the
                rest.

        """
        if mode == 'file':
            full_path = FileDialog(mode='open_file',
                                   filters=[u'*.ini']).exec_()
            if not full_path:
                return

            self.plugin.edited_measure = Measure.load_measure(self.plugin,
                                                              full_path)

        elif mode == 'template':
             # TODO create brand new measure using defaults from plugin and
            # load template
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

        core = self.workbench.getplugin('enaml.workbench.core')
        com = u'hqc_meas.instr_manager.drivers_request'
        res, drivers = core.invoke_command(com, {'drivers': list(drivs)}, self)
        if not res:
            mes = cleandoc('''Failed to get all drivers for the measure,
                           missing :{}'''.format(drivers))
            logger.info(mes)
            return False

        com = u'hqc_meas.instr_manager.profiles_request'
        res, profiles = core.invoke_command(com, {'profiles': list(profs)},
                                            self.plugin)
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
                            {'profiles': profiles}, self.plugin)

        if check:
            default_filename = measure.monitor.measure_name + '_last_run.ini'
            path = os.path.join(measure.root_task.default_path,
                                default_filename)
            measure.save_measure(path)
            meas = Measure.load_measure(self.workbench, path)
            # Here don't keep the profiles in the runtime as it will defeat the
            # purpose of the manager.
            meas.root_task.run_time = {'drivers': drivers}
            # Keep only a list of profiles to request (avoid to re-walk)
            meas.store['profiles'] = profs
            meas.status = 'READY'
            meas.infos = 'The measure is ready to be performed by an engine.'
            self.plugin.enqueued_measures.append(meas)

            return True

        else:
            ChecksDisplay(errors=errors).exec_()
            return False

    def reenqueue_measure(self, measure):
        """ Mark a measure already in queue as fitted to be executed.

        This method can be used to re-enqueue a measure that previously failed,
        for example becuse a profile was missing, the measure can then be
        edited again and will be executed in its turn.

        Parameters
        ----------
        measure : Measure
            The measure to re-enqueue

        """
        measure.enter_edition_state()
        measure.status = 'READY'
        measure.infos = 'Measure re-enqueued by the user'

    def start_processing_measures(self):
        """ Starts to perform the measurement in the queue.

        Measure will be processed in their order of appearance in the queue.

        """
        if not self.plugin.selected_engine:
            dial = EngineSelector(plugin=self.plugin)
            dial.exec_()
            if dial.selected_id:
                self.plugin.selected_engine = dial.selected_id
            else:
                logger = logging.getLogger(__name__)
                msg = cleandoc('''The user did not select an engine to run the
                               measure''')
                logger.warn(msg)
                return

        self.plugin.flags.clear()

        measure = self.plugin.find_next_measure()
        if measure is not None:
            self.plugin.start_measure()

    def process_single_measure(self, measure):
        """ Performs a single measurement and then stops.

        Parameters
        ----------
        index : int
            Index of the measurement to perform in the queue.

        """
        self.plugin.flags.clear()
        self.plugin.flags['stop_processing'] = True

        self.plugin.start_measure(measure)

    def stop_current_measure(self):
        """
        """
        self.plugin.stop_measure()

    def stop_processing_measures(self):
        """
        """
        self.plugin.stop_processing()

    def force_stop_measure(self):
        """
        """
        self.plugin.force_stop_measure()

    def force_stop_processing(self):
        """
        """
        self.plugin.force_stop_processing()

    @property
    def dock_area(self):
        """ Getter for the dock_area of the content.

        """
        if self.content:
            return self.content.children[0]
