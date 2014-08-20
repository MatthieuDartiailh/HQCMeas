# -*- coding: utf-8 -*-
#==============================================================================
# module : test_forms.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
import enaml
from nose.tools import assert_equal

with enaml.imports():
    from hqc_meas.instruments.manager_manifest import InstrManagerManifest
    from hqc_meas.instruments.profile_form import ProfileForm
    from hqc_meas.instruments.profile_edition import (ProfileView,
                                                      ProfileDialog)
    from hqc_meas.instruments.forms.base_forms import DummyForm

from ..util import complete_line
from .tools import BaseClass


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


class TestProfileForm(BaseClass):

    mod = __name__
    dir_id = 1

    def test_form1(self):
        self.workbench.register(InstrManagerManifest())
        manager = self.workbench.get_plugin(u'hqc_meas.instr_manager')
        form = ProfileForm(manager=manager)
        form.driver_type = 'Dummy'
        assert_equal(form.drivers, manager.matching_drivers(['Dummy']))
        assert isinstance(form.connection_form, DummyForm)
        assert_equal(form.dict(), {'name': '', 'driver_type': 'Dummy',
                                   'driver': ''})

    def test_view1(self):
        self.workbench.register(InstrManagerManifest())
        manager = self.workbench.get_plugin(u'hqc_meas.instr_manager')
        form = ProfileForm(manager=manager)
        view = ProfileView(form=form)
        del view
        view = ProfileView(form=form, mode='new')
        del view
        view = ProfileView(form=form, mode='edit')
        del view

    def test_dialog1(self):
        self.workbench.register(InstrManagerManifest())
        manager = self.workbench.get_plugin(u'hqc_meas.instr_manager')
        form = ProfileForm(manager=manager)
        view = ProfileDialog(model=form, mode='new')
        del view
        view = ProfileDialog(model=form, mode='edit')
        del view
