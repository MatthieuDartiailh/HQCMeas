# -*- coding: utf-8 -*-
from enaml.workbench.api import Workbench
import enaml
import os
import shutil
from configobj import ConfigObj
from nose.tools import assert_in, assert_not_in, assert_equal
from nose.plugins.skip import SkipTest

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from hqc_meas.utils.pref_manifest import PreferencesManifest
    from hqc_meas.task_management.manager_manifest import TaskManagerManifest

from ..util import complete_line


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
        os.mkdir(cls.test_dir)

        # Creating dummy default.ini file in utils.
        util_path = os.path.join(directory, '..', '..', 'hqc_meas', 'utils')
        def_path = os.path.join(util_path, 'default.ini')
        if os.path.isfile(def_path):
            os.rename(def_path, os.path.join(util_path, '__default.ini'))

        # Making the preference manager look for info in test dir.
        default = ConfigObj(def_path)
        default['folder'] = cls.test_dir
        default['file'] = 'default_test.ini'
        default.write()

        # Creating tasks preferences.
        task_path = os.path.join(directory, '..', '..', 'hqc_meas', 'tasks')
        task_api = set(('base_tasks.py', 'instr_task.py', 'tasks_util'))
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
        try:
            shutil.rmtree(cls.test_dir)

        # Hack for win32.
        except OSError:
            print 'OSError'
            dirs = os.listdir(cls.test_dir)
            for directory in dirs:
                shutil.rmtree(os.path.join(cls.test_dir), directory)
            shutil.rmtree(cls.test_dir)

        # Restoring default.ini file in utils
        directory = os.path.dirname(__file__)
        util_path = os.path.join(directory, '..', '..', 'hqc_meas', 'utils')
        def_path = os.path.join(util_path, 'default.ini')
        os.remove(def_path)

        aux = os.path.join(util_path, '__default.ini')
        if os.path.isfile(aux):
            os.rename(aux, def_path)

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
        assert_in('Print', plugin.tasks)
        assert_in('Definition', plugin.tasks)
        assert_in('Sleep', plugin.tasks)

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
        sleep(0.1)
        assert_in('Test',  plugin.tasks)
        assert_in('Template',  plugin.tasks)
        os.remove(os.path.join(template_path, 'test.ini'))
        sleep(0.1)
        assert_not_in('Test',  plugin.tasks)
        assert_in('Template',  plugin.tasks)

    def test_tasks_request1(self):
        self.workbench.register(TaskManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.task_manager.tasks_request'
        tasks = core.invoke_command(com, {'tasks': ['Complex', 'Sleep']},
                                    self)
        from hqc_meas.tasks.api import ComplexTask
        assert_equal(sorted(tasks.keys()), sorted(['Complex', 'Sleep']))
        assert_in(ComplexTask, tasks.values())

    def test_tasks_request2(self):
        self.workbench.register(TaskManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.task_manager.tasks_request'
        tasks = core.invoke_command(com, {'tasks': ['ComplexTask',
                                                    'SleepTask'],
                                          'use_class_names': True},
                                    self)
        from hqc_meas.tasks.api import ComplexTask
        assert_equal(sorted(tasks.keys()), sorted(['ComplexTask',
                     'SleepTask']))
        assert_in(ComplexTask, tasks.values())

    def test_views_request(self):
        self.workbench.register(TaskManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.task_manager.views_request'
        from hqc_meas.tasks.api import ComplexTask
        with enaml.imports():
            from hqc_meas.tasks.views.base_task_views import ComplexView
        views = core.invoke_command(com, {'task_classes': [ComplexTask]},
                                    self)
        assert_in(ComplexTask, views)
        assert_equal(views[ComplexTask], ComplexView)

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
        assert_in('Print', tasks)

        tasks = core.invoke_command(com, {'filter': 'Complex'}, self)
        assert_not_in('Print', tasks)
        assert_in('Complex', tasks)

        # Test the class attr filter
        tasks = core.invoke_command(com, {'filter': 'Loopable'}, self)
        assert_not_in('Definition', tasks)
        assert_in('Print', tasks)

    def test_config_request_build1(self):
        self.workbench.register(TaskManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.task_manager.config_request'

        conf, view = core.invoke_command(com, {'task': 'Print'}, self)
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
        conf.sub_task = 'Print'
        assert_equal(conf.config_ready, True)
        task = conf.build_task()
        assert_equal(task.task_name, 'Test')

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
