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
from logging.handlers import RotatingFileHandler
from multiprocessing import Process
from ..tools import MeasureSpy
from ..log_facility import (StreamToLogRedirector)


class TaskProcess(Process):
    """Process taking care of performing the measures.

    When started this process sets up a logger redirecting all records to a
    queue. It then redirects stdout and stderr to the logging system. Then as
    long as there is measures to perform  it asks the main process to send it
    measures through a pipe. Upon reception of the `ConfigObj` object
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
        while not self.process_stop.is_set():
            try:
                # Request a new measure to perform from the main process
                logger.info('Need task')
                self.pipe.send('Need task')

                # Get the answer
                self.pipe.poll(None)
                name, config, monitored_entries = self.pipe.recv()

                if config != 'STOP':
                    # If a real measurement was sent, build it.
                # TODO refactor this to work with collected datas
                    task = IniConfigTask().build_task_from_config(config)
                    logger.info('Task built')

                    # There are entries in the database we are supposed to
                    # monitor start a spy to do it.
                    if monitored_entries is not None:
                        spy = MeasureSpy(
                            self.monitor_queue, monitored_entries,
                            task.task_database)

                    # Set up the logger for this specific measurement.
                    if self.meas_log_handler is not None:
                        logger.removeHandler(self.meas_log_handler)
                        self.meas_log_handler.close()
                        self.meas_log_handler = None

                    log_path = os.path.join(
                        task.get_from_database('default_path'),
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

                    # Clear the event signaling the task it should stop, pass
                    # it to the task and make the database ready.
                    self.task_stop.clear()
                    task.should_stop = self.task_stop
                    task.task_database.prepare_for_running()

                    # Perform the checks.
                    check = task.check(test_instr=True)
                    if check[0]:
                        logger.info('Check successful')
                        # Perform the measure
                        task.process()
                        self.pipe.send('Task processed')
                        if self.task_stop.is_set():
                            logger.info('Task interrupted')
                        else:
                            logger.info('Task processed')
                    else:
                        fails = check[1].iteritems()
                        message = '\n'.join('{} : {}'.format(path, mes)
                                            for path, mes in fails)
                        logger.critical(message)

                    # If a spy was started kill it
                    if monitored_entries is not None:
                        spy.close()
                        del spy

            except IOError:
                pass

        # Clean up before closing.
        self.pipe.send('Closing')
        logger.info('Process shuting down')
        if self.meas_log_handler:
            self.meas_log_handler.close()
        self.log_queue.put_nowait(None)
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
                    'class': 'hqc_meas.log_facility.QueueHandler',
                    'queue': self.log_queue,
                },
            },
            'root': {
                'level': 'DEBUG',
                'handlers': ['queue']
            },
        }
        logging.config.dictConfig(config_worker)
        if os.name == 'posix':
            # On POSIX, the setup logger will have been configured in the
            # parent process, but should have been disabled following the
            # dictConfig call.
            # On Windows, since fork isn't used, the setup logger won't
            # exist in the child, so it would be created and the message
            # would appear - hence the "if posix" clause.
            logger = logging.getLogger('setup')
            logger.critical(
                'Should not appear, because of disabled logger ...')