# -*- coding: utf-8 -*-
# =============================================================================
# module : utils/log/test_plugin.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
import logging
from enaml.workbench.api import Workbench
from nose.tools import assert_equal
from enaml.qt.qt_application import QtApplication
import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.preferences.manifest import PreferencesManifest
    from hqc_meas.utils.log.manifest import LogManifest

from hqc_meas.utils.log.tools import (PanelModel, GuiHandler)
from ...util import complete_line


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


class Test(object):

    @classmethod
    def setup_class(cls):
        print complete_line(__name__ +
                            ':{}.setup_class()'.format(cls.__name__), '-', 77)

    @classmethod
    def teardown_class(cls):
        print complete_line(__name__ +
                            ':{}.teardown_class()'.format(cls.__name__), '-',
                            77)

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(LogManifest())

    def teardown(self):
        self.workbench.unregister(u'hqc_meas.logging')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_handler1(self):
        """ Test adding removing handler.

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        handler = GuiHandler(model=PanelModel())
        core.invoke_command(u'hqc_meas.logging.add_handler',
                            {'id': 'ui', 'handler': handler, 'logger': 'test'},
                            self)
        log_plugin = self.workbench.get_plugin(u'hqc_meas.logging')

        assert_equal(log_plugin.handler_ids, [u'ui'])
        assert_equal(log_plugin._handlers, {u'ui': (handler, 'test')})

        core.invoke_command(u'hqc_meas.logging.remove_handler',
                            {'id': 'ui'}, self)

        assert_equal(log_plugin.handler_ids, [])
        assert_equal(log_plugin._handlers, {})

    def test_handler2(self):
        """ Test adding removing handler.

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        core.invoke_command(u'hqc_meas.logging.add_handler',
                            {'id': 'ui', 'mode': 'ui', 'logger': 'test'},
                            self)
        log_plugin = self.workbench.get_plugin(u'hqc_meas.logging')

        assert_equal(log_plugin.handler_ids, [u'ui'])

        core.invoke_command(u'hqc_meas.logging.remove_handler',
                            {'id': 'ui'}, self)

        assert_equal(log_plugin.handler_ids, [])
        assert_equal(log_plugin._handlers, {})

    def test_handler3(self):
        """ Test adding removing handler.

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        core.invoke_command(u'hqc_meas.logging.add_handler',
                            {'id': 'ui', 'mode': 'ui', 'logger': 'test'},
                            self)
        log_plugin = self.workbench.get_plugin(u'hqc_meas.logging')

        assert_equal(log_plugin.handler_ids, [u'ui'])

        core.invoke_command(u'hqc_meas.logging.remove_handler',
                            {'id': 'ui'}, self)

        assert_equal(log_plugin.handler_ids, [])
        assert_equal(log_plugin._handlers, {})

    def test_filter1(self):
        """ Test adding removing filter.

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        handler = GuiHandler(model=PanelModel())
        core.invoke_command(u'hqc_meas.logging.add_handler',
                            {'id': 'ui', 'handler': handler, 'logger': 'test'},
                            self)

        class Filter(object):

            def filter(self, record):
                return True

        test_filter = Filter()

        core.invoke_command(u'hqc_meas.logging.add_filter',
                            {'id': 'filter', 'filter': test_filter,
                             'handler_id': 'ui'},
                            self)

        log_plugin = self.workbench.get_plugin(u'hqc_meas.logging')

        assert_equal(log_plugin.filter_ids, [u'filter'])
        assert_equal(log_plugin._filters, {u'filter': (test_filter, u'ui')})

        core.invoke_command(u'hqc_meas.logging.remove_filter',
                            {'id': 'filter'}, self)

        assert_equal(log_plugin.filter_ids, [])
        assert_equal(log_plugin._filters, {})

        core.invoke_command(u'hqc_meas.logging.remove_handler',
                            {'id': 'ui'}, self)

    def test_filter2(self):
        """ Test adding removing filter. Removing is done by removing the
        handler.

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        handler = GuiHandler(model=PanelModel())
        core.invoke_command(u'hqc_meas.logging.add_handler',
                            {'id': 'ui', 'handler': handler, 'logger': 'test'},
                            self)

        class Filter(object):

            def filter(self, record):
                return True

        test_filter = Filter()

        core.invoke_command(u'hqc_meas.logging.add_filter',
                            {'id': 'filter', 'filter': test_filter,
                             'handler_id': 'ui'},
                            self)

        log_plugin = self.workbench.get_plugin(u'hqc_meas.logging')

        assert_equal(log_plugin.filter_ids, [u'filter'])
        assert_equal(log_plugin._filters, {u'filter': (test_filter, u'ui')})

        core.invoke_command(u'hqc_meas.logging.remove_handler',
                            {'id': 'ui'}, self)

        assert_equal(log_plugin.filter_ids, [])
        assert_equal(log_plugin._filters, {})

    def test_formatter(self):
        """ Test setting the formatter of a handler.

        """
        if not QtApplication.instance():
            QtApplication()

        core = self.workbench.get_plugin(u'enaml.workbench.core')
        model = PanelModel()
        handler = GuiHandler(model=model)
        core.invoke_command(u'hqc_meas.logging.add_handler',
                            {'id': 'ui', 'handler': handler, 'logger': 'test'},
                            self)

        formatter = logging.Formatter('toto : %(message)s')
        core.invoke_command(u'hqc_meas.logging.set_formatter',
                            {'formatter': formatter, 'handler_id': 'ui'},
                            self)

        logger = logging.getLogger('test')
        logger.info('test')

        app = QtApplication.instance()._qapp
        app.flush()
        app.processEvents()

        core.invoke_command(u'hqc_meas.logging.remove_handler',
                            {'id': 'ui'}, self)

        assert_equal(model.text, 'toto : test\n')

    def test_start_logging(self):
        """ Minimal test for start logging.

        """
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        core.invoke_command(u'hqc_meas.logging.start_logging', {}, self)

        core.invoke_command(u'hqc_meas.logging.remove_handler',
                            {'id': 'standard'}, self)
