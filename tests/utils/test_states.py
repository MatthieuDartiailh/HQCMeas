# -*- coding: utf-8 -*-
from enaml.workbench.api import Workbench
import enaml

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from .states_utils import StateContributor, StateContributor2

CORE_PLUGIN = u'enaml.workbench.core'
GET_STATE = u'hqc_meas.state.get'


def setup_module():
    print __name__, ': setup_module() ~~~~~~~~~~~~~~~~~~~~~~'


def teardown_module():
    print __name__, ': teardown_module() ~~~~~~~~~~~~~~~~~~~'


class Test_State(object):

    @classmethod
    def setup_class(cls):
        print __name__, ': ', cls.__name__, '.setup_class() ----------'

    @classmethod
    def teardown_class(cls):
        print __name__, ': ', cls.__name__, 'teardown_class() -------'

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
        assert hasattr(state, 'string')
        assert hasattr(state, 'prop')

    def test_member_sync(self):
        core = self.workbench.get_plugin(CORE_PLUGIN)
        par = {'state_id': 'test.states.state'}
        state = core.invoke_command(GET_STATE,
                                    par, trigger=self)

        plugin = self.workbench.get_plugin('test.states')
        plugin.string = 'test'

        assert state.string == 'test'

    def test_prop_getter(self):
        core = self.workbench.get_plugin(CORE_PLUGIN)
        par = {'state_id': 'test.states.state'}
        state = core.invoke_command(GET_STATE,
                                    par, trigger=self)

        assert state.prop == 'ok'

    def test_death_notif1(self):
        core = self.workbench.get_plugin(CORE_PLUGIN)
        par = {'state_id': 'test.states.state'}
        state = core.invoke_command(GET_STATE,
                                    par, trigger=self)

        self.workbench.unregister(u'test.states')
        assert state.alive is False

    def test_death_notif2(self):
        self.workbench.register(StateContributor2())
        core = self.workbench.get_plugin(CORE_PLUGIN)
        par = {'state_id': 'test.states.state2'}
        state = core.invoke_command(GET_STATE,
                                    par, trigger=self)

        self.workbench.unregister(u'test.states2')
        assert state.alive is False
