# -*- coding: utf-8 -*-
#==============================================================================
# module : test_plugin.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
from enaml.workbench.api import Workbench
import enaml
import os
import shutil
from configobj import ConfigObj
from nose.tools import (assert_in, assert_not_in, assert_equal, raises,
                        assert_not_equal, assert_true, assert_false)
from nose.plugins.skip import SkipTest

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from hqc_meas.utils.pref_manifest import PreferencesManifest
    from hqc_meas.task_management.manager_manifest import TaskManagerManifest

    from .dummies import (DummyBuildDep1, DummyBuildDep1bis, DummyBuildDep2,
                          DummyBuildDep3, DummyBuildDep4, DummyBuildDep5,
                          DummyRuntimeDep1, DummyRuntimeDep1bis,
                          DummyRuntimeDep2, DummyRuntimeDep3,
                          DummyRuntimeDep4, DummyRuntimeDep5)

from ..util import complete_line, remove_tree, create_test_dir


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


class Test(object):

    test_dir = ''

    @classmethod
    def setup_class(cls):
        print complete_line(__name__ +
                            ':{}.setup_class()'.format(cls.__name__), '-', 77)
        # Creating dummy directory for prefs (avoid prefs interferences).
        directory = os.path.dirname(__file__)
        cls.test_dir = os.path.join(directory, '_temps')
        create_test_dir(cls.test_dir)

        # Creating dummy default.ini file in utils.
        util_path = os.path.join(directory, '..', '..', 'hqc_meas', 'utils')
        def_path = os.path.join(util_path, 'default.ini')

        # Making the preference manager look for info in test dir.
        default = ConfigObj(def_path)
        default['folder'] = cls.test_dir
        default['file'] = 'default_test.ini'
        default.write()

        # Creating tasks preferences.
        task_path = os.path.join(directory, '..', '..', 'hqc_meas', 'tasks')
        task_api = set(('base_tasks.py', 'instr_task.py', 'tasks_util',
                        'tasks_instr'))
        task_loading = [unicode('tasks.' + mod[:-3])
                        for mod in os.listdir(task_path)
                        if mod.endswith('.py') and mod not in task_api]
        task_loading.extend([unicode('tasks.' + pack)
                            for pack in os.listdir(task_path)
                            if os.path.isdir(os.path.join(task_path, pack))
                            and pack not in task_api])

        # Copying false template.
        template_path = os.path.join(cls.test_dir, 'temp_templates')
        os.mkdir(template_path)
        # Not in the root test dirt otherwise .ini got deleted ...
        # Not understood but unlinked to shutil.
        shutil.copyfile(os.path.join(directory, 'config_files',
                                     'template_ref.ini'),
                        os.path.join(template_path, 'template.ini'))

        # Saving plugin preferences.
        man_conf = {'tasks_loading': str(task_loading),
                    'templates_folders': str([template_path])}

        conf = ConfigObj(os.path.join(cls.test_dir, 'default_test.ini'))
        conf[u'hqc_meas.task_manager'] = {}
        conf[u'hqc_meas.task_manager'].update(man_conf)
        conf.write()

    @classmethod
    def teardown_class(cls):
        print complete_line(__name__ +
                            ':{}.teardown_class()'.format(cls.__name__), '-',
                            77)
        # Removing pref files creating during tests.
        remove_tree(cls.test_dir)

        # Restoring default.ini file in utils
        directory = os.path.dirname(__file__)
        util_path = os.path.join(directory, '..', '..', 'hqc_meas', 'utils')
        def_path = os.path.join(util_path, 'default.ini')
        os.remove(def_path)

    def setup(self):

        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())

    def teardown(self):
        self.workbench.unregister(u'hqc_meas.task_manager')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_init(self):
        self.workbench.register(TaskManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.task_manager')

        # Testing task explorations.
        assert_in('Complex', plugin.tasks)
        assert_not_in('Instr', plugin.tasks)
        assert_in('Log', plugin.tasks)
        assert_in('Definition', plugin.tasks)
        assert_in('Sleep', plugin.tasks)

        # Testing interface exploration
        assert_in('SetDCVoltageTask', plugin._task_interfaces)
        assert_not_equal(plugin._task_interfaces['SetDCVoltageTask'], [])

        # Testing templates
        assert_in('Template',  plugin.tasks)

    def test_load_all(self):
        self.workbench.register(TaskManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.task_manager')
        with plugin.suppress_notifications():
            plugin.views_loading = []
            plugin.tasks_loading = []

        plugin.notify('tasks_loading', {})

        if plugin.report():
            raise SkipTest(plugin.report())

    def test_template_observation(self):
        self.workbench.register(TaskManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.task_manager')
        assert_in('Template',  plugin.tasks)
        template_path = os.path.join(self.test_dir, 'temp_templates')
        prof = ConfigObj(os.path.join(template_path, 'test.ini'))
        prof.write()
        from time import sleep
        sleep(0.5)
        try:
            assert_in('Test',  plugin.tasks)
            assert_in('Template',  plugin.tasks)
        finally:
            os.remove(os.path.join(template_path, 'test.ini'))
        sleep(0.5)
        assert_not_in('Test',  plugin.tasks)
        assert_in('Template',  plugin.tasks)

    def test_tasks_request1(self):
        # Test requesting a task using its name.
        self.workbench.register(TaskManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.task_manager.tasks_request'
        tasks, miss = core.invoke_command(com, {'tasks': ['Complex', 'Sleep',
                                                          'XXXX']},
                                          self)
        from hqc_meas.tasks.api import ComplexTask
        assert_equal(sorted(tasks.keys()), sorted(['Complex', 'Sleep']))
        assert_in(ComplexTask, tasks.values())
        assert_equal(miss, ['XXXX'])

    def test_tasks_request2(self):
        # Test requesting a task using its class name.
        self.workbench.register(TaskManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.task_manager.tasks_request'
        tasks, miss = core.invoke_command(com, {'tasks': ['ComplexTask',
                                                          'SleepTask'],
                                                'use_class_names': True},
                                          self)
        from hqc_meas.tasks.api import ComplexTask
        assert_equal(sorted(tasks.keys()), sorted(['ComplexTask',
                     'SleepTask']))
        assert_in(ComplexTask, tasks.values())
        assert_equal(miss, [])

    def test_interface_request1(self):
        # Test requesting interfaces using the task class name
        self.workbench.register(TaskManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.task_manager.interfaces_request'
        interfaces, miss = core.invoke_command(com,
                                               {'tasks': ['SetDCVoltageTask',
                                                          'XXXX']},
                                               self)
        assert_equal(interfaces.keys(), ['SetDCVoltageTask'])
        assert_equal(miss, ['XXXX'])

    def test_interfaces_request2(self):
        # Test requesting interfaces using the interface class name
        self.workbench.register(TaskManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.task_manager.interfaces_request'
        kwargs = {'interfaces': ['MultiChannelVoltageSourceInterface']}
        inter, miss = core.invoke_command(com, kwargs, self)
        assert_equal(inter.keys(), ['MultiChannelVoltageSourceInterface'])

    def test_views_request(self):
        self.workbench.register(TaskManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.task_manager.views_request'
        with enaml.imports():
            from hqc_meas.tasks.views.base_task_views import ComplexView
        views, miss = core.invoke_command(com,
                                          {'task_classes': ['ComplexTask']},
                                          self)
        assert_in('ComplexTask', views)
        assert_equal(views['ComplexTask'], ComplexView)
        assert_equal(miss, [])

    def test_interface_views_request1(self):
        self.workbench.register(TaskManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.task_manager.interface_views_request'
        kwargs = {'interface_classes': ['MultiChannelVoltageSourceInterface']}
        views, miss = core.invoke_command(com, kwargs, self)
        assert_in('MultiChannelVoltageSourceInterface', views)
        assert_equal(miss, [])

    def test_filter_tasks(self):
        self.workbench.register(TaskManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.task_manager')
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.task_manager.filter_tasks'

        tasks = core.invoke_command(com, {'filter': 'All'}, self)
        assert_equal(sorted(tasks), sorted(plugin.tasks))

        tasks = core.invoke_command(com, {'filter': 'Python'}, self)
        assert_equal(sorted(tasks), sorted(plugin._py_tasks.keys()))

        tasks = core.invoke_command(com, {'filter': 'Template'}, self)
        assert_equal(sorted(tasks), sorted(plugin._template_tasks.keys()))

        # These two tests are sufficient to ensure that subclass tests works
        tasks = core.invoke_command(com, {'filter': 'Simple'}, self)
        assert_not_in('Complex', tasks)
        assert_in('Log', tasks)

        tasks = core.invoke_command(com, {'filter': 'Complex'}, self)
        assert_not_in('Log', tasks)
        assert_in('Complex', tasks)

        # Test the class attr filter
        tasks = core.invoke_command(com, {'filter': 'Loopable'}, self)
        assert_not_in('Definition', tasks)
        assert_in('Log', tasks)

    def test_config_request_build1(self):
        self.workbench.register(TaskManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.task_manager.config_request'

        conf, view = core.invoke_command(com, {'task': 'Log'}, self)
        assert_equal(type(conf).__name__, 'PyConfigTask')
        conf.task_name = 'Test'
        assert_equal(conf.config_ready, True)
        task = conf.build_task()
        assert_equal(task.task_name, 'Test')

    def test_config_request_build2(self):
        self.workbench.register(TaskManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.task_manager.config_request'

        conf, view = core.invoke_command(com, {'task': 'Template'}, self)
        assert_equal(type(conf).__name__, 'IniConfigTask')
        conf.task_name = 'Test'
        assert_equal(conf.config_ready, True)
        task = conf.build_task()
        assert_equal(task.task_name, 'Test')
        assert_equal(len(task.children_task), 1)
        task2 = task.children_task[0]
        assert_equal(task2.task_name, 'a')
        assert_equal(task2.task_class, 'LogTask')

    def test_config_request_build3(self):
        self.workbench.register(TaskManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.task_manager.config_request'

        plugin = self.workbench.get_plugin(u'hqc_meas.task_manager')
        if u'tasks.tasks_logic' in plugin.tasks_loading:
            aux = plugin.tasks_loading[:]
            aux.remove(u'tasks.tasks_logic')
            plugin.tasks_loading = aux

        conf, view = core.invoke_command(com, {'task': 'Loop'}, self)
        assert_equal(type(conf).__name__, 'LoopConfigTask')
        conf.task_name = 'Test'
        conf.subtask = 'Log'
        assert_equal(conf.config_ready, True)
        task = conf.build_task()
        assert_equal(task.task_name, 'Test')

    def test_collect_dependencies(self):
        # Test collecting build dependencies.
        self.workbench.register(TaskManagerManifest())
        from hqc_meas.tasks.api import RootTask, ComplexTask
        from hqc_meas.tasks.tasks_util.log_task import LogTask
        aux = [LogTask(task_name='r')]
        root = RootTask(task_name='root')
        root.children_task = [ComplexTask(task_name='complex',
                                          children_task=aux),
                              LogTask(task_name='t')]

        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.task_manager.collect_dependencies'
        res, build, run = core.invoke_command(com, {'task': root}, core)
        assert_true(res)
        assert_in('tasks', build)
        assert_equal(sorted(['LogTask', 'ComplexTask']),
                     sorted(build['tasks'].keys()))
        assert_not_in('interfaces', build)
        assert_false(run)

    # --- Test BuildDependencies ----------------------------------------------

    def test_build_dep_registation1(self):
        # Test that build deps are properly found at start-up.

        self.workbench.register(TaskManagerManifest())
        self.workbench.register(DummyBuildDep1())
        plugin = self.workbench.get_plugin(u'hqc_meas.task_manager')

        manager = plugin._build_dep_manager

        assert_in(u'dummy.build_dep1', manager.collectors)

        self.workbench.unregister(u'dummy.build_dep1')

        assert_not_in(u'dummy.build_dep1', manager.collectors)

    def test_build_dep_registration2(self):
        # Test build deps update when a new plugin is registered.

        self.workbench.register(TaskManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.task_manager')
        self.workbench.register(DummyBuildDep1())

        manager = plugin._build_dep_manager

        assert_in(u'dummy.build_dep1', manager.collectors)

        self.workbench.unregister(u'dummy.build_dep1')

        assert_not_in(u'dummy.build_dep1', manager.collectors)

    def test_build_dep_factory(self):
        # Test getting the BuildDependency decl from a factory.

        self.workbench.register(TaskManagerManifest())
        self.workbench.register(DummyBuildDep2())
        plugin = self.workbench.get_plugin(u'hqc_meas.task_manager')

        manager = plugin._build_dep_manager

        assert_in(u'dummy.build_dep2', manager.collectors)

        self.workbench.unregister(u'dummy.build_dep2')

        assert_not_in(u'dummy.build_dep1', manager.collectors)

    @raises(ValueError)
    def test_build_dep_errors1(self):
        # Test uniqueness of BuildDependency id.

        self.workbench.register(TaskManagerManifest())
        self.workbench.register(DummyBuildDep1())
        self.workbench.register(DummyBuildDep1bis())
        self.workbench.get_plugin(u'hqc_meas.task_manager')

    @raises(ValueError)
    def test_build_dep_errors2(self):
        # Test presence of dependencies in BuildDependency.

        self.workbench.register(TaskManagerManifest())
        self.workbench.register(DummyBuildDep3())
        self.workbench.get_plugin(u'hqc_meas.task_manager')

    @raises(ValueError)
    def test_build_dep_errors3(self):
        # Test presence of collect in BuildDependency.

        self.workbench.register(TaskManagerManifest())
        self.workbench.register(DummyBuildDep4())
        self.workbench.get_plugin(u'hqc_meas.task_manager')

    @raises(TypeError)
    def test_build_dep_errors4(self):
        # Test enforcement of type for BuildDependency when using factory.

        self.workbench.register(TaskManagerManifest())
        self.workbench.register(DummyBuildDep5())
        self.workbench.get_plugin(u'hqc_meas.task_manager')

    # --- Test RuntimeDependencies --------------------------------------------

    def test_runtime_dep_registation1(self):
        # Test that runtime deps are properly found at start-up.

        self.workbench.register(TaskManagerManifest())
        self.workbench.register(DummyRuntimeDep1())
        plugin = self.workbench.get_plugin(u'hqc_meas.task_manager')

        manager = plugin._runtime_dep_manager

        assert_in(u'dummy.runtime_dep1', manager.collectors)

        self.workbench.unregister(u'dummy.runtime_dep1')

        assert_not_in(u'dummy.runtime_dep1', manager.collectors)
        assert_equal(manager._extensions, {})

    def test_runtime_dep_registration2(self):
        # Test runtime deps update when a new plugin is registered.

        self.workbench.register(TaskManagerManifest())
        plugin = self.workbench.get_plugin(u'hqc_meas.task_manager')
        self.workbench.register(DummyRuntimeDep1())

        manager = plugin._runtime_dep_manager

        assert_in(u'dummy.runtime_dep1', manager.collectors)

        self.workbench.unregister(u'dummy.runtime_dep1')

        assert_not_in(u'dummy.runtime_dep1', manager.collectors)

    def test_runtime_dep_factory(self):
        # Test getting the RuntimeDependency decl from a factory.

        self.workbench.register(TaskManagerManifest())
        self.workbench.register(DummyRuntimeDep2())
        plugin = self.workbench.get_plugin(u'hqc_meas.task_manager')

        manager = plugin._runtime_dep_manager

        assert_in(u'dummy.runtime_dep2', manager.collectors)

        self.workbench.unregister(u'dummy.runtime_dep2')

        assert_not_in(u'dummy.runtime_dep2', manager.collectors)

    @raises(ValueError)
    def test_runtime_dep_errors1(self):
        # Test uniqueness of RuntimeDependency id.

        self.workbench.register(TaskManagerManifest())
        self.workbench.register(DummyRuntimeDep1())
        self.workbench.register(DummyRuntimeDep1bis())
        self.workbench.get_plugin(u'hqc_meas.task_manager')

    @raises(ValueError)
    def test_runtime_dep_errors2(self):
        # Test presence of dependencies in RuntimeDependency.

        self.workbench.register(TaskManagerManifest())
        self.workbench.register(DummyRuntimeDep3())
        self.workbench.get_plugin(u'hqc_meas.task_manager')

    @raises(ValueError)
    def test_runtime_dep_errors3(self):
        # Test presence of collect in RuntimeDependency.

        self.workbench.register(TaskManagerManifest())
        self.workbench.register(DummyRuntimeDep4())
        self.workbench.get_plugin(u'hqc_meas.task_manager')

    @raises(TypeError)
    def test_runtime_dep_errors4(self):
        # Test enforcement of type for RuntimeDependency when using factory.

        self.workbench.register(TaskManagerManifest())
        self.workbench.register(DummyRuntimeDep5())
        self.workbench.get_plugin(u'hqc_meas.task_manager')

    # Cannot test this as it would require UI must test lower level
#    def test_save_task(self):
#        self.workbench.register(TaskManagerManifest())
#
#
#    def test_build_task(self):
#        self.workbench.register(TaskManagerManifest())

#    # config mode only
#    def test_build_root(self):
#        self.workbench.register(TaskManagerManifest())
