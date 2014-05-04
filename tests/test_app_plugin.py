# -*- coding: utf-8 -*-
from enaml.workbench.api import Workbench
from enaml.widgets.window import CloseEvent
import enaml
from nose.tools import assert_equal, assert_false, assert_true, raises

with enaml.imports():
    from hqc_meas.app_manifest import HqcAppManifest
    from .app_helpers import (ClosingContributor1, ClosingContributor1bis,
                              ClosingContributor2, ClosingContributor3,
                              ClosingContributor4)

from .util import complete_line


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


class Helper(object):

    def __init__(self, workbench):
        self.workbench = workbench


class Test_Prefs(object):

    test_dir = ''

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

    def test_closing(self):
        """ Test that validation stops as soon as the event is rejected.

        """
        self.workbench.register(HqcAppManifest())
        self.workbench.register(ClosingContributor1())
        self.workbench.register(ClosingContributor2())
        manifest1 = self.workbench.get_manifest('test.closing')
        manifest2 = self.workbench.get_manifest('test.closing2')
        window = Helper(self.workbench)

        plugin = self.workbench.get_plugin('hqc_meas.app')
        ev = CloseEvent()
        plugin.validate_closing(window, ev)

        assert_false(ev.is_accepted())
        assert_false(manifest2.called)

        manifest1.accept = True
        manifest2.accept = True

        plugin.validate_closing(window, ev)

        assert_true(ev.is_accepted())
        assert_true(manifest2.called)

        self.workbench.unregister(u'test.closing')
        self.workbench.unregister(u'hqc_meas.app')

    def test_check_registation1(self):
        """ Test that ClosingApp are properly found at start-up.

        """
        self.workbench.register(HqcAppManifest())
        self.workbench.register(ClosingContributor1())

        plugin = self.workbench.get_plugin('hqc_meas.app')
        assert_equal(len(plugin._closing_extensions), 1)
        assert_equal(len(plugin._closing_checks), 1)

        self.workbench.unregister(u'test.closing')

        assert_false(plugin._closing_extensions)
        assert_false(plugin._closing_checks)

        self.workbench.unregister(u'hqc_meas.app')

    def test_check_registration2(self):
        """ Test ClosingApp update when a new plugin is registered.

        """
        self.workbench.register(HqcAppManifest())

        plugin = self.workbench.get_plugin('hqc_meas.app')
        assert_false(plugin._closing_extensions)
        assert_false(plugin._closing_checks)

        self.workbench.register(ClosingContributor1())
        assert_equal(len(plugin._closing_extensions), 1)
        assert_equal(len(plugin._closing_checks), 1)

        self.workbench.unregister(u'test.closing')
        self.workbench.unregister(u'hqc_meas.app')

    def test_check_factory(self):
        """ Test getting the ClosingApp decl from a factory.

        """
        self.workbench.register(HqcAppManifest())
        self.workbench.register(ClosingContributor2())

        plugin = self.workbench.get_plugin('hqc_meas.app')
        assert_equal(len(plugin._closing_extensions), 1)
        assert_equal(len(plugin._closing_checks), 1)

        self.workbench.unregister(u'test.closing2')

        assert_false(plugin._closing_extensions)
        assert_false(plugin._closing_checks)

        self.workbench.unregister(u'hqc_meas.app')

    @raises(ValueError)
    def test_check_errors1(self):
        """ Test uniqueness of ClosingApp id.

        """
        self.workbench.register(HqcAppManifest())
        self.workbench.register(ClosingContributor1())
        self.workbench.register(ClosingContributor1bis())
        self.workbench.get_plugin(u'hqc_meas.app')

    @raises(ValueError)
    def test_check_errors2(self):
        """ Test presence of validate in ClosingApp.

        """
        self.workbench.register(HqcAppManifest())
        self.workbench.register(ClosingContributor3())
        self.workbench.get_plugin(u'hqc_meas.app')

    @raises(TypeError)
    def test_check_errors3(self):
        """ Test enforcement of type for ClosingApp when using factory.

        """
        self.workbench.register(HqcAppManifest())
        self.workbench.register(ClosingContributor4())
        self.workbench.get_plugin(u'hqc_meas.app')
