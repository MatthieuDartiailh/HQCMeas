# -*- coding: utf-8 -*-
# =============================================================================
# module : utils/dependencies/test_plugin.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from enaml.workbench.api import Workbench
import enaml
from nose.tools import (assert_in, assert_not_in, assert_equal, raises)

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.dependencies.manifest import DependenciesManifest

    from .dummies import (DummyBuildDep1, DummyBuildDep1bis, DummyBuildDep2,
                          DummyBuildDep3, DummyBuildDep4, DummyBuildDep5,
                          DummyRuntimeDep1, DummyRuntimeDep1bis,
                          DummyRuntimeDep2, DummyRuntimeDep3,
                          DummyRuntimeDep4, DummyRuntimeDep5)


class TestPlugin(object):

    def setup(self):

        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(DependenciesManifest())

    def teardown(self):
        self.workbench.unregister(u'hqc_meas.dependencies')
        self.workbench.unregister(u'enaml.workbench.core')

    # --- Test BuildDependencies ----------------------------------------------

    def test_build_dep_registation1(self):
        # Test that build deps are properly found at start-up.

        self.workbench.register(DummyBuildDep1())
        plugin = self.workbench.get_plugin(u'hqc_meas.dependencies')

        assert_in(u'dummy.build_dep1', plugin.build_collectors)

        self.workbench.unregister(u'dummy.build_dep1')

        assert_not_in(u'dummy.build_dep1', plugin.build_collectors)

    def test_build_dep_registration2(self):
        # Test build deps update when a new plugin is registered.

        plugin = self.workbench.get_plugin(u'hqc_meas.dependencies')
        self.workbench.register(DummyBuildDep1())

        assert_in(u'dummy.build_dep1', plugin.build_collectors)

        self.workbench.unregister(u'dummy.build_dep1')

        assert_not_in(u'dummy.build_dep1', plugin.build_collectors)

    def test_build_dep_factory(self):
        # Test getting the BuildDependency decl from a factory.

        self.workbench.register(DummyBuildDep2())
        plugin = self.workbench.get_plugin(u'hqc_meas.dependencies')

        assert_in(u'dummy.build_dep2', plugin.build_collectors)

        self.workbench.unregister(u'dummy.build_dep2')

        assert_not_in(u'dummy.build_dep1', plugin.build_collectors)

    @raises(ValueError)
    def test_build_dep_errors1(self):
        # Test uniqueness of BuildDependency id.

        self.workbench.register(DummyBuildDep1())
        self.workbench.register(DummyBuildDep1bis())
        self.workbench.get_plugin(u'hqc_meas.dependencies')

    @raises(ValueError)
    def test_build_dep_errors2(self):
        # Test presence of dependencies in BuildDependency.

        self.workbench.register(DummyBuildDep3())
        self.workbench.get_plugin(u'hqc_meas.dependencies')

    @raises(ValueError)
    def test_build_dep_errors3(self):
        # Test presence of collect in BuildDependency.

        self.workbench.register(DummyBuildDep4())
        self.workbench.get_plugin(u'hqc_meas.dependencies')

    @raises(TypeError)
    def test_build_dep_errors4(self):
        # Test enforcement of type for BuildDependency when using factory.

        self.workbench.register(DummyBuildDep5())
        self.workbench.get_plugin(u'hqc_meas.dependencies')

    # --- Test RuntimeDependencies --------------------------------------------

    def test_runtime_dep_registation1(self):
        # Test that runtime deps are properly found at start-up.

        self.workbench.register(DummyRuntimeDep1())
        plugin = self.workbench.get_plugin(u'hqc_meas.dependencies')

        assert_in(u'dummy.runtime_dep1', plugin.runtime_collectors)

        self.workbench.unregister(u'dummy.runtime_dep1')

        assert_not_in(u'dummy.runtime_dep1', plugin.runtime_collectors)
        assert_equal(plugin._runtime_extensions, {})

    def test_runtime_dep_registration2(self):
        # Test runtime deps update when a new plugin is registered.

        plugin = self.workbench.get_plugin(u'hqc_meas.dependencies')
        self.workbench.register(DummyRuntimeDep1())

        assert_in(u'dummy.runtime_dep1', plugin.runtime_collectors)

        self.workbench.unregister(u'dummy.runtime_dep1')

        assert_not_in(u'dummy.runtime_dep1', plugin.runtime_collectors)

    def test_runtime_dep_factory(self):
        # Test getting the RuntimeDependency decl from a factory.

        self.workbench.register(DummyRuntimeDep2())
        plugin = self.workbench.get_plugin(u'hqc_meas.dependencies')

        assert_in(u'dummy.runtime_dep2', plugin.runtime_collectors)

        self.workbench.unregister(u'dummy.runtime_dep2')

        assert_not_in(u'dummy.runtime_dep2', plugin.runtime_collectors)

    @raises(ValueError)
    def test_runtime_dep_errors1(self):
        # Test uniqueness of RuntimeDependency id.

        self.workbench.register(DummyRuntimeDep1())
        self.workbench.register(DummyRuntimeDep1bis())
        self.workbench.get_plugin(u'hqc_meas.dependencies')

    @raises(ValueError)
    def test_runtime_dep_errors2(self):
        # Test presence of dependencies in RuntimeDependency.

        self.workbench.register(DummyRuntimeDep3())
        self.workbench.get_plugin(u'hqc_meas.dependencies')

    @raises(ValueError)
    def test_runtime_dep_errors3(self):
        # Test presence of collect in RuntimeDependency.

        self.workbench.register(DummyRuntimeDep4())
        self.workbench.get_plugin(u'hqc_meas.dependencies')

    @raises(TypeError)
    def test_runtime_dep_errors4(self):
        # Test enforcement of type for RuntimeDependency when using factory.

        self.workbench.register(DummyRuntimeDep5())
        self.workbench.get_plugin(u'hqc_meas.dependencies')
