# -*- coding: utf-8 -*-
#==============================================================================
# module : subprocess.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
import os
import logging
import logging.config
import warnings
import sys
# TODO write my own rotating file handler to work under windows
from logging.handlers import RotatingFileHandler
from multiprocessing import Process

from hqc_meas.log_system.tools import (StreamToLogRedirector)
from hqc_meas.task_management.config.api import IniConfigTask
from ..tools import MeasureSpy


class TaskProcess(Process):
    """Process taking care of performing the measures.

    When started this process sets up a logger redirecting all records to a
    queue. It then redirects stdout and stderr to the logging system. Then as
    long as it is not stopped it waits for the main process to send a
    measures through the pipe. Upon reception of the `ConfigObj` object
    describing the measure it rebuilds it, set up a logger for that specific
    measure and if necessary starts a spy transmitting the value of all
    monitored entries to the main process. It finally run the checks of the
    measure and run it. It can be interrupted by setting an event and upon
    exit close the communication pipe and signal all listeners that it is
    closing.

    Parameters
    ----------
    pipe : double ended multiprocessing pipe
        Pipe used to communicate with the parent process which is transferring
        the measure to perform.
    log_queue : multiprocessing queue
        Queue in which all log records are sent to be procesed later in the
        main process.
    monitor_queue : multiprocessing queue
        Queue in which all the informations the user asked to monitor during
        the measurement are sent to be processed in the main process.
    task_stop : multiprocessing event
        Event set when the user asked the running measurement to stop.
    process_stop : multiprocessing event
        Event set when the user asked the process to stop.

    Attributes
    ----------
    meas_log_handler : log handler
        Log handler used to save the running measurement specific records.
    see `Parameters`

    Methods
    -------
    run():
        Method called when the new process starts.

    """

    def __init__(self, pipe, log_queue, monitor_queue,
                 task_stop, process_stop):
        super(TaskProcess, self).__init__(name='MeasureProcess')
        self.task_stop = task_stop
        self.process_stop = process_stop
        self.pipe = pipe
        self.log_queue = log_queue
        self.monitor_queue = monitor_queue
        self.meas_log_handler = None

    def run(self):
        """Method called when the new process starts.

        For a complete description of the workflow see the class
        docstring.

        """
        self._config_log()
        # Ugly patch to avoid pyvisa complaining about missing filters
        warnings.simplefilter("ignore")

        # Redirecting stdout and stderr to the logging system.
        logger = logging.getLogger()
        redir_stdout = StreamToLogRedirector(logger)
        sys.stdout = redir_stdout
        logger.info('Logger parametrised')

        logger.info('Process running')
        self.pipe.send('READY')
        while not self.process_stop.is_set():

            # Prevent us from crash if the pipe is closed at the wrong moment.
            try:

                # Wait for a measurement.
                while not self.pipe.poll(2):
                    if self.process_stop.is_set():
                        break

                if self.process_stop.is_set():
                    break

                # Get the measure.
                name, config, runtimes, monitored_entries = self.pipe.recv()

                # Build it by first extracting task classes from runtimes.
                tasks = runtimes.pop('task_classes')
                builder = IniConfigTask(task_classes=tasks)
                root = builder.build_task_from_config(config)

                # Give all runtime dependencies to the root task.
                root.run_time = runtimes

                logger.info('Task built')

                # There are entries in the database we are supposed to
                # monitor start a spy to do it.
                if monitored_entries:
                    spy = MeasureSpy(
                        self.monitor_queue, monitored_entries,
                        root.task_database)

                # Set up the logger for this specific measurement.
                if self.meas_log_handler is not None:
                    logger.removeHandler(self.meas_log_handler)
                    self.meas_log_handler.close()
                    self.meas_log_handler = None

                log_path = os.path.join(
                    root.get_from_database('default_path'),
                    name + '.log')
                if os.path.isfile(log_path):
                    os.remove(log_path)
                self.meas_log_handler = RotatingFileHandler(log_path,
                                                            mode='w',
                                                            maxBytes=10**6,
                                                            backupCount=10)
                aux = '%(asctime)s | %(levelname)s | %(message)s'
                formatter = logging.Formatter(aux)
                self.meas_log_handler.setFormatter(formatter)
                logger.addHandler(self.meas_log_handler)

                # Pass the event signaling the task it should stop
                # to the task and make the database ready.
                root.should_stop = self.task_stop
                root.task_database.prepare_for_running()

                # Perform the checks.
                check, errors = root.check(test_instr=True)

                # They pass perform the measure.
                if check:
                    logger.info('Check successful')
                    meas_result = root.process()
                    result = ['', '', '']
                    if self.task_stop.is_set():
                        result[0] = 'INTERRUPTED'
                        result[2] = 'Measure {} was stopped'.format(name)
                    else:
                        if meas_result:
                            result[0] = 'COMPLETED'
                            result[2] = 'Measure {} succeeded'.format(name)
                        else:
                            result[0] = 'FAILED'
                            result[2] = 'Measure {} failed'.format(name)

                    if self.process_stop.is_set():
                        result[1] = 'STOPPING'
                    else:
                        result[1] = 'READY'

                    self.pipe.send(tuple(result))

                # They fail, mark the measure as failed and go on.
                else:
                    mes = 'Tests failed see log for full records.'
                    self.pipe.send(('FAILED', 'READY', mes))

                    # Log the tests that failed.
                    fails = errors.iteritems()
                    message = '\n'.join('{} : {}'.format(path, mes)
                                        for path, mes in fails)
                    logger.critical(message)

                # If a spy was started kill it
                if monitored_entries:
                    spy.close()
                    del spy

            except IOError:
                pass

        # Clean up before closing.
        logger.info('Process shuting down')
        if self.meas_log_handler:
            self.meas_log_handler.close()
        self.log_queue.put_nowait(None)
        self.monitor_queue.put_nowait((None, None))
        self.pipe.close()

    def _config_log(self):
        """Configuring the logger for the process.

        Sending all record to a multiprocessing queue.

        """
        config_worker = {
            'version': 1,
            'disable_existing_loggers': True,
            'handlers': {
                'queue': {
                    'class': 'hqc_meas.log_system.tools.QueueHandler',
                    'queue': self.log_queue,
                },
            },
            'root': {
                'level': 'DEBUG',
                'handlers': ['queue']
            },
        }
        logging.config.dictConfig(config_worker)
#        if os.name == 'posix':
#            # On POSIX, the setup logger will have been configured in the
#            # parent process, but should have been disabled following the
#            # dictConfig call.
#            # On Windows, since fork isn't used, the setup logger won't
#            # exist in the child, so it would be created and the message
#            # would appear - hence the "if posix" clause.
#            logger = logging.getLogger('setup')
#            logger.critical(
#                'Should not appear, because of disabled logger ...')
