# -*- coding: utf-8 -*-
#==============================================================================
# module : test_states.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from enaml.workbench.api import Workbench
from nose.tools import assert_equal, assert_true, assert_is
import enaml

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from .states_utils import StateContributor, StateContributor2

from ..util import complete_line

CORE_PLUGIN = u'enaml.workbench.core'
GET_STATE = u'hqc_meas.state.get'


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


class Test_State(object):

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
        self.workbench.register(StateManifest())
        self.workbench.register(StateContributor())

    def teardown(self):
        pass

    def test_get_state(self):
        core = self.workbench.get_plugin(CORE_PLUGIN)
        par = {'state_id': 'test.states.state'}
        assert core.invoke_command(GET_STATE,
                                   par, trigger=self)

    def test_state_content(self):
        core = self.workbench.get_plugin(CORE_PLUGIN)
        par = {'state_id': 'test.states.state'}
        state = core.invoke_command(GET_STATE,
                                    par, trigger=self)
        assert_true(hasattr(state, 'string'))
        assert_equal(state.string, 'init')
        assert_true(hasattr(state, 'prop'))

    def test_member_sync(self):
        core = self.workbench.get_plugin(CORE_PLUGIN)
        par = {'state_id': 'test.states.state'}
        state = core.invoke_command(GET_STATE,
                                    par, trigger=self)

        plugin = self.workbench.get_plugin('test.states')
        plugin.string = 'test'

        assert_equal(state.string, 'test')

    def test_prop_getter(self):
        core = self.workbench.get_plugin(CORE_PLUGIN)
        par = {'state_id': 'test.states.state'}
        state = core.invoke_command(GET_STATE,
                                    par, trigger=self)

        assert_equal(state.prop, 'ok')

    def test_death_notif1(self):
        core = self.workbench.get_plugin(CORE_PLUGIN)
        par = {'state_id': 'test.states.state'}
        state = core.invoke_command(GET_STATE,
                                    par, trigger=self)

        self.workbench.unregister(u'test.states')
        assert_is(state.alive, False)

    def test_death_notif2(self):
        self.workbench.register(StateContributor2())
        core = self.workbench.get_plugin(CORE_PLUGIN)
        par = {'state_id': 'test.states.state2'}
        state = core.invoke_command(GET_STATE,
                                    par, trigger=self)

        self.workbench.unregister(u'test.states2')
        assert_is(state.alive, False)
