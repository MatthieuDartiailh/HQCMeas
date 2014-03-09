# -*- coding: utf-8 -*-
#==============================================================================
# module : test_manager_view.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
import enaml

from .tools import BaseClass

with enaml.imports():
    from hqc_meas.instruments.manager_manifest import InstrManagerManifest
    from hqc_meas.instruments.manager_view import InstrManagerView


class TestManagerView(BaseClass):

    mod  = __name__

    def test_form1(self):
        self.workbench.register(InstrManagerManifest())
        manager = self.workbench.get_plugin(u'hqc_meas.instr_manager')
        view = InstrManagerView(manager=manager)
        del view
