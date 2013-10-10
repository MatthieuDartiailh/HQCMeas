# -*- coding: utf-8 -*-
#==============================================================================
# module : connection_forms.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
This module defines some tools to make easier the use of the logging module
in the program, first by seamlessly converting stream information into log
record so that any `print` can get recorded. And also by defining tools to
process log emitted in the measure process.

:Contains:
    StreamToLogRedirector
        Simple class to redirect a stream to a logger.
    QueueHandler
        Logger handler putting records into a queue.
    GuiConsoleHandler
        Logger handler adding the message of a record to a GUI panel.
    QueueLoggerThread
        Thread getting log record from a queue and asking logging to handle them
"""

import logging
from inspect import cleandoc
from threading import Thread

class StreamToLogRedirector(object):
    """Simple class to redirect a stream to a logger.

    Stream like object which can be used to replace `sys.stdout`, or
    `sys.stderr`.

    Parameters
    ----------
    logger : instance(`Logger`)
        Instance of a loger object returned by a call to logging.getLogger
    stream_type : {'stdout', 'stderr'}, optionnal
        Type of stream being redirected. Stderr stream are logged as CRITICAL

    Attributes
    ----------
    logger : instance(`Logger`)
        Instance of a loger used to log the received message
    level : {logging.INFO, logging.CRITICAL}
        Default level to which logs the received messages

    Methods
    -------
    write(message)
        Log the received message to the correct level
    flush()
        Useless method implemented for compatibilty

    """
    def __init__(self, logger, stream_type = 'stdout'):
        self.logger =  logger
        if stream_type == 'stderr':
            self.level = logging.CRITICAL
        else:
            self.level = logging.INFO

    def write(self, message):
        """Record the received message using the logger stored in `logger`

        The received message is first strip of starting and trailing whitespaces
        and line return. If `level` is `logging.CRITICAL` the message is
        directly logged, otherwise the message is parsed to look for the
        following markers, corresponding to logging levels : '<DEBUG>',
        '<WARNING>', '<ERROR>', '<CRITICAL>'. This allows to use different
        logging levels using print.
        """
        message = message.strip()
        if message != '':
            if self.level != logging.CRITICAL:
                if '<DEBUG>' in message:
                    message = message.replace('<DEBUG>','').strip()
                    self.logger.warning(message)
                elif '<WARNING>' in message:
                    message = message.replace('<WARNING>','').strip()
                    self.logger.warning(message)
                elif '<ERROR>' in message:
                    message = message.replace('<ERROR>','').strip()
                    self.logger.error(message)
                elif '<CRITICAL>' in message:
                    message = message.replace('<ERROR>','').strip()
                    self.logger.critical(message)
                else:
                    self.logger.log(self.level, message)
            else:
                self.logger.log(self.level, message)

    def flush(self):
        """Useless function implemented for compatibility
        """
        return None

# Copied and pasted from the logging module of Python 3.3
class QueueHandler(logging.Handler):
    """
    This handler sends events to a queue. Typically, it would be used together
    with a multiprocessing Queue to centralise logging to file in one process
    (in a multi-process application), so as to avoid file write contention
    between processes.

    """

    def __init__(self, queue):
        """
        Initialise an instance, using the passed queue.
        """
        logging.Handler.__init__(self)
        self.queue = queue

    def enqueue(self, record):
        """
        Enqueue a record.

        The base implementation uses put_nowait. You may want to override
        this method if you want to use blocking, timeouts or custom queue
        implementations.

        """
        self.queue.put_nowait(record)

    def prepare(self, record):
        """
        Prepares a record for queueing. The object returned by this
        method is enqueued.
        The base implementation formats the record to merge the message
        and arguments, and removes unpickleable items from the record
        in-place.
        You might want to override this method if you want to convert
        the record to a dict or JSON string, or send a modified copy
        of the record while leaving the original intact.

        """
        # The format operation gets traceback text into record.exc_text
        # (if there's exception data), and also puts the message into
        # record.message. We can then use this to replace the original
        # msg + args, as these might be unpickleable. We also zap the
        # exc_info attribute, as it's no longer needed and, if not None,
        # will typically not be pickleable.
        self.format(record)
        record.msg = record.message
        record.args = None
        record.exc_info = None
        return record

    def emit(self, record):
        """
        Emit a record.

        Writes the LogRecord to the queue, preparing it first.
        """
        try:
            self.enqueue(self.prepare(record))
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

class GuiConsoleHandler(logging.Handler):
    """Logger record sending the log message to a GUI panel

    Parameters
    ----------
    process_panel_dict : dict(str, GUIPanel)
        Dict mapping process names to GUIPanel (object with a string attribute)
        where the message should be displayed.

    Methods
    -------
    emit(record)
        Handle a log record by appending the log message to the GUIPanel

    """
    def __init__(self, process_panel_dict):
        logging.Handler.__init__(self)
        self.process_panel_dict = process_panel_dict

    def emit(self, record):
        """
        Write the log record message to the appropriate GUIPanel according to
        the process they are issued from. Record with a critical level, likely
        to have caused the program to crash, are not displayed but the user is
        encouraged to check the log file.

        """
        panel = self.process_panel_dict[record.processName]
        try:
            if record.levelname == 'INFO':
                panel.string += record.message + '\n'
            elif record.levelname == 'CRITICAL':
                panel.string += cleandoc('''An error occured please check the
                                log file for more details.''') + '\n'
            else:
                panel.string += record.levelname + ':' + \
                                                record.message + '\n'
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class QueueLoggerThread(Thread):
    """Worker thread emptying a queue containing log record and asking the
    appropriate logger to handle them.

    """

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        """
        Pull any output from the queue while the listened process does not put
        `None` into the queue
        """
        while True:
            #Collect all display output from process
            record = self.queue.get()
            if record is None:
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)