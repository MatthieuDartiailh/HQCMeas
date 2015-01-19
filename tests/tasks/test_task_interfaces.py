# -*- coding: utf-8 -*-
# =============================================================================
# module : test_task_interfaces.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from atom.api import Bool, set_default
from nose.tools import (assert_equal, assert_true, assert_false,
                        assert_is)

from hqc_meas.tasks.api import ComplexTask, RootTask
from hqc_meas.tasks.task_interface import InterfaceableTaskMixin, TaskInterface


class InterfaceTest(TaskInterface):

    answer = Bool()

    called = Bool()

    interface_database_entries = set_default({'itest': 1.0})

    def check(self, *args, **kwargs):
        self.called = True

        if self.answer:
            return True, {}
        else:
            return False, {'i': 0}


class InterfaceTest2(TaskInterface):

    interface_database_entries = set_default({'itest': 2.0})


class Mixin(InterfaceableTaskMixin, ComplexTask):

    task_database_entries = set_default({'test': 2.0})


class IMixin(InterfaceableTaskMixin, ComplexTask):

    task_database_entries = set_default({'test': 2.0})

    def i_perform(self):
        pass


class TestInterfaceableTaskMixin(object):

    def setup(self):
        self.root = RootTask()
        self.mixin = Mixin(task_name='Simple')
        self.root.children_task = [self.mixin]

    def test_interface_observer(self):
        i1 = InterfaceTest()
        i2 = InterfaceTest2()

        self.mixin.interface = i1
        assert_is(i1.task, self.mixin)
        assert_equal(self.mixin.task_database_entries,
                     {'test': 2.0, 'itest': 1.0})

        self.mixin.interface = i2
        assert_is(i2.task, self.mixin)
        assert_is(i1.task, None)
        assert_equal(self.mixin.task_database_entries,
                     {'test': 2.0, 'itest': 2.0})

    def test_check1(self):
        # Test everything ok if interface present.
        self.mixin.interface = InterfaceTest(answer=True)

        res, traceback = self.mixin.check()
        assert_true(res)
        assert_false(traceback)
        assert_true(self.mixin.interface.called)

    def test_check2(self):
        # Test everything is ok if i_perform method exists.
        res, traceback = IMixin().check()
        assert_true(res)
        assert_false(traceback)

    def test_check3(self):
        # Test handling missing interface.
        res, traceback = self.mixin.check()
        assert_false(res)
        assert_true(traceback)
        assert_equal(len(traceback), 1)

    def test_check4(self):
        # Test handling a non-passing test from the interface.
        self.mixin.interface = InterfaceTest()

        res, traceback = self.mixin.check()
        assert_false(res)
        assert_true(traceback)
        assert_equal(len(traceback), 1)
        assert_true(self.mixin.interface.called)

    def test_build_from_config1(self):
        # Test building a interfaceable task from a config.
        aux = RootTask()
        aux.children_task = [IMixin()]
        bis = RootTask.build_from_config(aux.task_preferences,
                                         {'tasks': {'IMixin': IMixin,
                                                    'RootTask': RootTask}})
        assert_equal(type(bis.children_task[0]).__name__, 'IMixin')
