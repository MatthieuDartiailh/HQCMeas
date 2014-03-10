# -*- coding: utf-8 -*-
from enaml.workbench.api import Workbench
import enaml
import os
import shutil
from configobj import ConfigObj
from nose.tools import assert_in, assert_not_in, assert_equal

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state_manifest import StateManifest
    from hqc_meas.utils.pref_manifest import PreferencesManifest
    from hqc_meas.task_management.manager_manifest import TaskManagerManifest


def setup_module():
    print __name__, ': setup_module() ~~~~~~~~~~~~~~~~~~~~~~'


def teardown_module():
    print __name__, ': teardown_module() ~~~~~~~~~~~~~~~~~~~'


class Test_TaskManagement(object):

    test_dir = ''

    @classmethod
    def setup_class(cls):
        print __name__, ': TestClass.setup_class() ----------'
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
        shutil.copyfile(os.path.join(directory, 'template_ref.ini'),
                        os.path.join(template_path, 'template.ini'))

        # Saving plugin preferences.
        man_conf = {'tasks_loading': str(task_loading),
                    'templates_folders': str([template_path])}

        conf = ConfigObj(os.path.join(cls.test_dir, 'default_test.ini'))
        conf[u'hqc_meas.task_manager'] = {}
        conf[u'hqc_meas.task_manager'].update(man_conf)
        conf.write()

    # TODO find why template_ref.ini disappear (not linked to rmtree)
    @classmethod
    def teardown_class(cls):
        print '\n', __name__, ': TestClass.teardown_class() -------'
         # Removing pref files creating during tests.
#        try:
#            shutil.rmtree(cls.test_dir)
#
#        # Hack for win32.
#        except OSError:
#            dirs = os.listdir(cls.test_dir)
#            for directory in dirs:
#                shutil.rmtree(os.path.join(cls.test_dir), directory)
#            shutil.rmtree(cls.test_dir)

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

    def test_tasks_request(self):
        self.workbench.register(TaskManagerManifest())
        core = self.workbench.get_plugin(u'enaml.workbench.core')
        com = u'hqc_meas.task_manager.tasks_request'
        tasks = core.invoke_command(com, {'tasks': ['Complex', 'Sleep']},
                                    self)
        from hqc_meas.tasks.api import ComplexTask
        assert_equal(sorted(tasks.keys()), sorted(['Complex', 'Sleep']))
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

    # TODO still to write (use internl storage for filters and config)
    def test_filter_tasks(self):
        self.workbench.register(TaskManagerManifest())

    def test_config_request(self):
        self.workbench.register(TaskManagerManifest())

    def test_save_task(self):
        self.workbench.register(TaskManagerManifest())

    def test_build_task(self):
        self.workbench.register(TaskManagerManifest())

    def test_build_root(self):
        self.workbench.register(TaskManagerManifest())
