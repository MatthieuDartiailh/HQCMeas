# -*- coding: utf-8 -*-

import sys
import logging
from multiprocessing import Queue
from nose.tools import assert_equal, with_setup
from enaml.qt.qt_application import QtApplication
from hqc_meas.log_system.tools import (StreamToLogRedirector, QueueHandler,
                                       PanelModel, DayRotatingTimeHandler,
                                       GuiHandler, QueueLoggerThread)

from ..util import complete_line


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


def teardown():
    logger = logging.getLogger('test')
    logger.handlers = []


@with_setup(teardown=teardown)
def test_gui_handler():
    """ Test the gui handler.

    """
    model = PanelModel()
    handler = GuiHandler(model)
    logger = logging.getLogger('test')
    logger.addHandler(handler)
    qapp = QtApplication.instance()._qapp

    logger.info('test')
    qapp.flush()
    qapp.processEvents()
    assert_equal(model.text, 'test\n')
    model.text = ''

    logger.debug('test')
    qapp.flush()
    qapp.processEvents()
    assert_equal(model.text, 'DEBUG: test\n')
    model.text = ''

    logger.warn('test')
    qapp.flush()
    qapp.processEvents()
    assert_equal(model.text, 'WARNING: test\n')
    model.text = ''

    logger.error('test')
    qapp.flush()
    qapp.processEvents()
    assert_equal(model.text, 'ERROR: test\n')
    model.text = ''

    logger.critical('test')
    qapp.flush()
    qapp.processEvents()
    answer = 'An error occured please check the log file for more details.\n'
    assert_equal(model.text, answer)
    model.text = ''


@with_setup(teardown=teardown)
def test_stream_redirection1():
    """ Test the redirection of a stream toward a logger : INFO.

    """
    model = PanelModel()
    handler = GuiHandler(model)
    logger = logging.getLogger('test')
    logger.addHandler(handler)
    qapp = QtApplication.instance()._qapp
    stdout = sys.stdout
    sys.stdout = StreamToLogRedirector(logger)

    try:
        print 'test'
    finally:
        sys.stdout = stdout

    qapp.flush()
    qapp.processEvents()
    assert_equal(model.text, 'test\n')


@with_setup(teardown=teardown)
def test_stream_redirection2():
    """ Test the redirection of a stream toward a logger : DEBUG.

    """
    model = PanelModel()
    handler = GuiHandler(model)
    logger = logging.getLogger('test')
    logger.addHandler(handler)
    qapp = QtApplication.instance()._qapp
    stdout = sys.stdout
    sys.stdout = StreamToLogRedirector(logger)

    try:
        print '<DEBUG>test'
    finally:
        sys.stdout = stdout

    qapp.flush()
    qapp.processEvents()
    assert_equal(model.text, 'DEBUG: test\n')


@with_setup(teardown=teardown)
def test_stream_redirection3():
    """ Test the redirection of a stream toward a logger : WAARNING.

    """
    model = PanelModel()
    handler = GuiHandler(model)
    logger = logging.getLogger('test')
    logger.addHandler(handler)
    qapp = QtApplication.instance()._qapp
    stdout = sys.stdout
    sys.stdout = StreamToLogRedirector(logger)

    try:
        print '<WARNING>test'
    finally:
        sys.stdout = stdout

    qapp.flush()
    qapp.processEvents()
    assert_equal(model.text, 'WARNING: test\n')


@with_setup(teardown=teardown)
def test_stream_redirection4():
    """ Test the redirection of a stream toward a logger : ERROR.

    """
    model = PanelModel()
    handler = GuiHandler(model)
    logger = logging.getLogger('test')
    logger.addHandler(handler)
    qapp = QtApplication.instance()._qapp
    stdout = sys.stdout
    sys.stdout = StreamToLogRedirector(logger)

    try:
        print '<ERROR>test'
    finally:
        sys.stdout = stdout

    qapp.flush()
    qapp.processEvents()
    assert_equal(model.text, 'ERROR: test\n')


@with_setup(teardown=teardown)
def test_stream_redirection5():
    """ Test the redirection of a stream toward a logger : CRITICAL.

    """
    model = PanelModel()
    handler = GuiHandler(model)
    logger = logging.getLogger('test')
    logger.addHandler(handler)
    qapp = QtApplication.instance()._qapp
    stdout = sys.stdout
    sys.stdout = StreamToLogRedirector(logger)

    try:
        print '<CRITICAL>test'
    finally:
        sys.stdout = stdout

    qapp.flush()
    qapp.processEvents()
    answer = 'An error occured please check the log file for more details.\n'
    assert_equal(model.text, answer)


@with_setup(teardown=teardown)
def test_stream_redirection6():
    """ Test the redirection of a stream toward a logger, stderr.

    """
    model = PanelModel()
    handler = GuiHandler(model)
    logger = logging.getLogger('test')
    logger.addHandler(handler)
    qapp = QtApplication.instance()._qapp
    stdout = sys.stdout
    sys.stdout = StreamToLogRedirector(logger, stream_type='stderr')

    try:
        print '<CRITICAL>test'
    finally:
        sys.stdout = stdout

    qapp.flush()
    qapp.processEvents()
    answer = 'An error occured please check the log file for more details.\n'
    assert_equal(model.text, answer)


@with_setup(teardown=teardown)
def test_queue_handler():
    """ Test the queue handler.

    """
    logger = logging.getLogger('test')
    queue = Queue()
    handler = QueueHandler(queue)
    logger.addHandler(handler)
    logger.info('test')

    record = queue.get()
    assert_equal(record.message, 'test')


@with_setup(teardown=teardown)
def test_logger_thread():
    """ Test the logger thread.

    """
    logger = logging.getLogger('test')
    queue = Queue()
    handler = QueueHandler(queue)
    logger.addHandler(handler)
    logger.info('test')
    logger.removeHandler(handler)
    queue.put(None)

    model = PanelModel()
    handler = GuiHandler(model)
    logger.addHandler(handler)

    thread = QueueLoggerThread(queue)
    thread.start()
    thread.join(2)

    if thread.is_alive():
        raise

    qapp = QtApplication.instance()._qapp
    qapp.flush()
    qapp.processEvents()

    assert_equal(model.text, 'test\n')

# TODO add test for DayRotating
