# -*- coding: utf-8 -*-
# ============================================================
# module : test_save_tasks.py
# author : Matthieu Dartiailh
# license : MIT license
# ============================================================
"""
"""
from nose.tools import (assert_equal, assert_true, assert_false, assert_in,
                        assert_not_in, assert_raises)
from nose.plugins.attrib import attr
from multiprocessing import Event
from enaml.workbench.api import Workbench
import os
import shutil
import numpy as np

from hqc_meas.tasks.api import RootTask
from hqc_meas.tasks.tasks_util.save_tasks import (SaveTask, SaveArrayTask,
                                                  SaveFileTask)

import enaml
with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from hqc_meas.utils.state.manifest import StateManifest
    from hqc_meas.utils.preferences.manifest import PreferencesManifest
    from hqc_meas.tasks.manager.manifest import TaskManagerManifest

    from hqc_meas.tasks.tasks_util.views.save_views import (SaveView,
                                                            SaveArrayView,
                                                            SaveFileView)

from ...util import process_app_events, close_all_windows, complete_line


TEST_PATH = os.path.join(os.path.dirname(__file__), 'files')


class TestSaveTask(object):

    test_dir = TEST_PATH

    @classmethod
    def setup_class(cls):
        print complete_line(__name__ +
                            ':{}.setup_class()'.format(cls.__name__), '-', 77)
        os.mkdir(cls.test_dir)

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

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SaveTask(task_name='Test')
        self.root.children_task.append(self.task)

        self.root.write_in_database('int', 1)
        self.root.write_in_database('float', 2.0)
        self.root.write_in_database('str', 'a')

    def teardown(self):
        folder = self.test_dir
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            if os.path.isfile(file_path):
                os.remove(file_path)

    def test_saving_target_observer(self):
        self.task.saving_target = 'Array'

        assert_equal(self.task.get_from_database('Test_array'),
                     np.array([1.0]))

        self.task.saving_target = 'File'

        aux = self.task.accessible_database_entries()
        assert_not_in('Test_array', aux)

        self.task.saving_target = 'File and array'

        assert_equal(self.task.get_from_database('Test_array'),
                     np.array([1.0]))

    def test_check1(self):
        # Test everything ok in file mode (no array size).
        task = self.task
        task.saving_target = 'File'
        task.folder = self.test_dir
        task.filename = 'test{Root_int}.txt'
        task.file_mode = 'New'
        task.header = 'test'
        task.saved_values = [('toto', '{Root_str}'), ('tata', '{Root_float}')]
        file_path = os.path.join(self.test_dir, 'test1.txt')

        test, traceback = task.check()
        assert_true(test)
        assert_false(traceback)
        assert_false(os.path.isfile(file_path))
        assert_false(task.initialized)

        task.file_mode = 'Add'

        test, traceback = task.check()
        assert_true(test)
        assert_false(traceback)
        assert_true(os.path.isfile(file_path))
        os.remove(file_path)

    def test_check2(self):
        # Test everything of in array mode (assert database state).
        task = self.task
        task.saving_target = 'Array'
        task.array_size = '1000*{Root_float}'
        task.saved_values = [('toto', '{Root_str}'), ('tata', '{Root_float}')]

        test, traceback = task.check()
        assert_true(test)
        assert_false(traceback)
        array = task.get_from_database('Test_array')
        assert_equal(array.dtype.names, ('toto', 'tata'))

    def test_check3(self):
        # Test everything is ok in file & array mode.
        task = self.task
        task.saving_target = 'File and array'
        task.folder = self.test_dir
        task.filename = 'test_rr.txt'
        task.file_mode = 'New'
        task.header = 'test'
        task.array_size = '1000*{Root_float}'
        task.saved_values = [('toto', '{Root_str}'), ('tata', '{Root_float}')]
        file_path = os.path.join(self.test_dir, 'test_rr.txt')

        test, traceback = task.check()
        assert_true(test)
        assert_false(traceback)
        assert_false(os.path.isfile(file_path))
        array = task.get_from_database('Test_array')
        assert_equal(array.dtype.names, ('toto', 'tata'))

    def test_check4(self):
        # Test check issues in file mode : folder.
        task = self.task
        task.saving_target = 'File'
        task.folder = self.test_dir + '{tt}'

        test, traceback = task.check()
        assert_false(test)
        assert_true(traceback)
        assert_equal(len(traceback), 1)

    def test_check5(self):
        # Test check issues in file mode : file.
        task = self.task
        task.saving_target = 'File'
        task.folder = self.test_dir
        task.filename = 'test{tt}.txt'

        test, traceback = task.check()
        assert_false(test)
        assert_true(traceback)
        assert_equal(len(traceback), 1)

    def test_check6(self):
        # Test check issues in file mode : array_size.
        task = self.task
        task.saving_target = 'File'
        task.folder = self.test_dir
        task.filename = 'test.txt'
        task.file_mode = 'New'
        task.header = 'test'
        task.array_size = '1000*'
        task.saved_values = [('toto', '{Root_str}'), ('tata', '{Root_float}')]
        file_path = os.path.join(self.test_dir, 'test.txt')

        test, traceback = task.check()
        assert_false(test)
        assert_true(traceback)
        assert_equal(len(traceback), 1)
        assert_false(os.path.isfile(file_path))

    def test_check6bis(self):
        # Test check issues in file mode : header formatting.
        task = self.task
        task.saving_target = 'File'
        task.folder = self.test_dir
        task.filename = 'test.txt'
        task.file_mode = 'New'
        task.header = 'test {*}'
        task.array_size = '1000'
        task.saved_values = [('toto', '{Root_str}'), ('tata', '{Root_float}')]
        file_path = os.path.join(self.test_dir, 'test.txt')

        test, traceback = task.check()
        assert_false(test)
        assert_true(traceback)
        assert_equal(len(traceback), 1)
        assert_false(os.path.isfile(file_path))

    def test_check7(self):
        # Test check issues in array mode  : wrong array_size.
        task = self.task
        task.saving_target = 'Array'
        task.array_size = '1000*{Root_float}*'
        task.saved_values = [('toto', '{Root_str}'), ('tata', '{Root_float}')]

        test, traceback = task.check()
        assert_false(test)
        assert_true(traceback)
        assert_equal(len(traceback), 1)
        assert_equal(self.task.get_from_database('Test_array'),
                     np.array([1.0]))

    def test_check8(self):
        # Test check issues in array mode : absent array_size.
        task = self.task
        task.saving_target = 'Array'
        task.saved_values = [('toto', '{Root_str}'), ('tata', '{Root_float}')]

        test, traceback = task.check()
        assert_false(test)
        assert_true(traceback)
        assert_equal(len(traceback), 1)
        assert_equal(self.task.get_from_database('Test_array'),
                     np.array([1.0]))

    def test_check9(self):
        # Test check issues in entrie.
        task = self.task
        task.saving_target = 'Array'
        task.array_size = '1000*{Root_float}'
        task.saved_values = [('toto', '{Root_str*}'),
                             ('tata', '{Root_float*}')]

        test, traceback = task.check()
        assert_false(test)
        assert_true(traceback)
        assert_equal(len(traceback), 2)
        array = task.get_from_database('Test_array')
        assert_equal(array.dtype.names, ('toto', 'tata'))

    def test_check10(self):
        # Test warning in case the file already exists in new mode.
        task = self.task
        task.saving_target = 'File'
        task.folder = self.test_dir
        task.filename = 'test_e.txt'
        task.file_mode = 'New'
        task.header = 'test'
        task.saved_values = [('toto', '{Root_str}'), ('tata', '{Root_float}')]
        file_path = os.path.join(self.test_dir, 'test_e.txt')
        with open(file_path, 'w'):
            pass

        assert_true(os.path.isfile(file_path))
        test, traceback = task.check()
        assert_true(test)
        assert_true(traceback)
        assert_true(os.path.isfile(file_path))

    def test_perform1(self):
        # Test performing in mode file. (Call three times perform)
        task = self.task
        task.saving_target = 'File'
        task.folder = self.test_dir
        task.filename = 'test_perform{Root_int}.txt'
        task.file_mode = 'Add'
        task.header = 'test {Root_str}'
        task.array_size = '3'
        task.saved_values = [('toto', '{Root_str}'), ('tata', '{Root_float}')]
        file_path = os.path.join(self.test_dir, 'test_perform1.txt')

        with open(file_path, 'w') as f:
            f.write('test\n')

        task.perform()

        assert_true(task.initialized)
        assert_true(task.file_object)
        assert_equal(task.line_index, 1)
        with open(file_path) as f:
            a = f.readlines()
            assert_equal(a,
                         ['test\n', '# test a\n', 'toto\ttata\n', 'a\t2.0\n'])

        task.perform()

        assert_true(task.initialized)
        assert_equal(task.line_index, 2)
        with open(file_path) as f:
            a = f.readlines()
            assert_equal(a, ['test\n', '# test a\n', 'toto\ttata\n',
                             'a\t2.0\n', 'a\t2.0\n'])

        task.perform()

        assert_false(task.initialized)
        assert_equal(task.line_index, 3)
        with open(file_path) as f:
            a = f.readlines()
            assert_equal(a, ['test\n', '# test a\n', 'toto\ttata\n',
                             'a\t2.0\n', 'a\t2.0\n', 'a\t2.0\n'])

    def test_perform2(self):
        # Test performing in array mode. (Call three times perform)
        task = self.task
        task.saving_target = 'Array'
        task.array_size = '3'
        task.saved_values = [('toto', '{Root_int}'), ('tata', '{Root_float}')]

        task.perform()

        assert_true(task.initialized)
        assert_equal(task.line_index, 1)

        task.perform()

        assert_true(task.initialized)
        assert_equal(task.line_index, 2)

        task.perform()

        assert_false(task.initialized)
        assert_equal(task.line_index, 3)

        array_type = np.dtype([(str(s[0]), 'f8')
                               for s in task.saved_values])
        array = np.empty((3),  dtype=array_type)
        array[0] = (1, 2.0)
        array[1] = (1, 2.0)
        array[2] = (1, 2.0)
        np.testing.assert_array_equal(task.array, array)


class TestSaveFileTask(object):

    test_dir = TEST_PATH + '2'

    @classmethod
    def setup_class(cls):
        print complete_line(__name__ +
                            ':{}.setup_class()'.format(cls.__name__), '-', 77)
        os.mkdir(cls.test_dir)

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

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SaveFileTask(task_name='Test')
        self.root.children_task.append(self.task)

        self.root.write_in_database('int', 1)
        self.root.write_in_database('float', 2.0)
        self.root.write_in_database('array', np.array(range(10)))

    def teardown(self):
        folder = self.test_dir
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            if os.path.isfile(file_path):
                os.remove(file_path)

    def test_check1(self):
        # Test everything ok in file mode (no array size).
        task = self.task
        task.folder = self.test_dir
        task.filename = 'test{Root_int}.txt'
        task.saved_values = [('toto', '{Root_int}'), ('tata', '{Root_float}')]
        file_path = os.path.join(self.test_dir, 'test1.txt')

        test, traceback = task.check()
        assert_true(test)
        assert_false(traceback)
        assert_false(os.path.isfile(file_path))
        assert_false(task.initialized)

    def test_check4(self):
        # Test check issues in file mode : folder.
        task = self.task
        task.folder = self.test_dir + '{tt}'

        test, traceback = task.check()
        assert_false(test)
        assert_true(traceback)
        assert_equal(len(traceback), 1)

    def test_check5(self):
        # Test check issues in file mode : file.
        task = self.task
        task.folder = self.test_dir
        task.filename = 'test{tt}.txt'

        test, traceback = task.check()
        assert_false(test)
        assert_true(traceback)
        assert_equal(len(traceback), 1)

    def test_check6(self):
        # Test check issues in file mode : header formatting.
        task = self.task
        task.folder = self.test_dir
        task.filename = 'test.txt'
        task.header = 'test {*}'

        test, traceback = task.check()
        assert_false(test)
        assert_true(traceback)
        assert_equal(len(traceback), 1)

    def test_check9(self):
        # Test check issues in entries.
        task = self.task
        task.folder = self.test_dir
        self.root.write_in_database('int', 3)
        task.filename = 'test{Root_int}.txt'
        task.saved_values = [('toto', '{Root_int*}'),
                             ('tata', '{Root_float*}')]

        test, traceback = task.check()
        assert_false(test)
        assert_true(traceback)
        assert_equal(len(traceback), 2)

    def test_check10(self):
        # Test warning in case the file already exists in new mode.
        task = self.task
        task.folder = self.test_dir
        task.filename = 'test_e.txt'
        task.header = 'test'
        task.saved_values = [('toto', '{Root_int}'), ('tata', '{Root_float}')]
        file_path = os.path.join(self.test_dir, 'test_e.txt')
        with open(file_path, 'w'):
            pass

        assert_true(os.path.isfile(file_path))
        test, traceback = task.check()
        print traceback
        assert_true(test)
        assert_true(traceback)
        assert_true(os.path.isfile(file_path))

    def test_perform1(self):
        # Test performing with non rec array. (Call twice perform)
        task = self.task
        task.folder = self.test_dir
        task.filename = 'test_perform{Root_int}.txt'
        task.header = 'test {Root_float}'
        task.saved_values = [('toto', '{Root_float}'),
                             ('tata', '{Root_array}')]
        file_path = os.path.join(self.test_dir, 'test_perform1.txt')

        with open(file_path, 'w') as f:
            f.write('test\n')

        try:
            task.perform()

            assert_true(task.initialized)
            assert_true(task.file_object)
            with open(file_path) as f:
                a = f.readlines()

            assert_equal(a[:2], ['# test 2.0\n',
                                 'toto\ttata\n'])
            for i in range(10):
                assert_equal(float(a[2+i].split('\t')[0]), 2.0)
                assert_equal(float(a[2+i].split('\t')[1]), float(i))

            task.perform()

            assert_true(task.initialized)
            with open(file_path) as f:
                a = f.readlines()
            assert_equal(float(a[12].split('\t')[0]), 2.0)
            assert_equal(float(a[12].split('\t')[1]), 0.0)

            task.perform()
        finally:
            task.file_object.close()

    def test_perform2(self):
        # Test performing with a rec array. (Call twice perform)
        self.root.write_in_database('array',
                                    np.rec.fromarrays([range(10), range(10)],
                                                      names=['a', 'b']))
        task = self.task
        task.folder = self.test_dir
        task.filename = 'test_perform_rec.txt'
        task.header = 'test'
        task.saved_values = [('toto', '{Root_float}'),
                             ('tata', '{Root_array}')]
        file_path = os.path.join(self.test_dir, 'test_perform_rec.txt')

        with open(file_path, 'w') as f:
            f.write('test\n')

        try:
            task.perform()

            assert_true(task.initialized)
            assert_true(task.file_object)
            with open(file_path) as f:
                a = f.readlines()

            assert_equal(a[:2], ['# test\n',
                                 'toto\ttata_a\ttata_b\n'])
            for i in range(10):
                assert_equal(float(a[2+i].split('\t')[0]), 2.0)
                assert_equal(float(a[2+i].split('\t')[1]), float(i))

            task.perform()

            assert_true(task.initialized)
            with open(file_path) as f:
                a = f.readlines()

            assert_equal(float(a[12].split('\t')[0]), 2.0)
            assert_equal(float(a[12].split('\t')[1]), 0.0)

            task.perform()
        finally:
            task.file_object.close()


class TestSaveArrayTask(object):

    test_dir = TEST_PATH

    @classmethod
    def setup_class(cls):
        print complete_line(__name__ +
                            ':{}.setup_class()'.format(cls.__name__), '-', 77)
        os.mkdir(cls.test_dir)

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

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SaveArrayTask(task_name='Test')
        self.root.children_task.append(self.task)

        array = np.empty(2, dtype=np.dtype([('a', 'f8'), ('b', 'f8')]))
        array[0] = (0, 1)
        array[1] = (2, 3)
        self.root.write_in_database('array', array)
        self.root.write_in_database('float', 2.0)
        self.root.write_in_database('str', 'a')

    def teardown(self):
        folder = self.test_dir
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            if os.path.isfile(file_path):
                os.remove(file_path)

    def test_check1(self):
        # Check everything ok in Text mode.
        array = np.empty(2, dtype=np.dtype([('a', 'f8'), ('b', 'f8')]))
        self.root.write_in_database('arrays', {'a': array})
        task = self.task
        task.folder = self.test_dir
        task.filename = 'test_perform{Root_str}.txt'
        task.mode = 'Text file'
        task.header = 'teststs'
        task.target_array = '{Root_arrays}["a"]'

        test, traceback = task.check()

        assert_true(test)
        assert_false(traceback)
        assert_false(os.path.isfile(os.path.join(self.test_dir,
                                                 'test_performa.txt')))

    def test_check2(self):
        # Check everything ok in Binary mode (wrong file extension, and header)
        task = self.task
        task.folder = self.test_dir
        task.filename = 'test_perform{Root_str}.txt'
        task.mode = 'Binary file'
        task.header = 'teststs'
        task.target_array = '{Root_array}'

        test, traceback = task.check()

        assert_true(test)
        assert_equal(len(traceback), 2)
        assert_in('root/Test-header', traceback)
        assert_in('root/Test-file_ext', traceback)
        assert_false(os.path.isfile(os.path.join(self.test_dir,
                                                 'test_performa.npy')))

    def test_check3(self):
        # Check handling a wrong folder.
        task = self.task
        task.folder = self.test_dir + '{eee}'

        test, traceback = task.check()

        assert_false(test)
        assert_equal(len(traceback), 1)

    def test_check4(self):
        # Check handling a wrong filename.
        task = self.task
        task.folder = self.test_dir
        task.filename = '{rr}'

        test, traceback = task.check()

        assert_false(test)
        assert_equal(len(traceback), 1)

    def test_check5(self):
        # Check handling a wrong database address.
        task = self.task
        task.folder = self.test_dir
        task.filename = 'test_perform{Root_str}.txt'
        task.mode = 'Text file'
        task.header = 'teststs'
        task.target_array = '**{Root_array}'

        test, traceback = task.check()

        assert_false(test)
        assert_equal(len(traceback), 1)

    def test_check6(self):
        # Check handling a wrong type.
        self.root.write_in_database('array', 1.0)
        task = self.task
        task.folder = self.test_dir
        task.filename = 'test_perform{Root_str}.txt'
        task.mode = 'Text file'
        task.header = 'teststs'
        task.target_array = '{Root_array}'

        test, traceback = task.check()

        assert_false(test)
        assert_equal(len(traceback), 1)

    def test_perform1(self):
        # Test performing in text mode.
        task = self.task
        task.folder = self.test_dir
        task.filename = 'test_perform{Root_str}.txt'
        task.mode = 'Text file'
        task.header = 'tests'
        task.target_array = '{Root_array}'

        task.perform()

        path = os.path.join(self.test_dir, 'test_performa.txt')
        assert_true(os.path.isfile(path))
        with open(path) as f:
            lines = f.readlines()
            assert_equal(lines[0:2], ['# tests\n', 'a\tb\n'])
            assert_equal([float(x) for x in lines[2][:-1].split('\t')],
                         [0.0, 1.0])
            assert_equal([float(x) for x in lines[3][:-1].split('\t')],
                         [2.0, 3.0])

    def test_perform1bis(self):
        # Test performing in text mode wrong type.
        self.root.write_in_database('array', 1.0)
        task = self.task
        task.folder = self.test_dir
        task.filename = 'test_perform{Root_str}.txt'
        task.mode = 'Text file'
        task.header = 'tests'
        task.target_array = '{Root_array}'

        assert_raises(AssertionError, task.perform)

    def test_perform2(self):
        # Test performing in binary mode.
        task = self.task
        task.folder = self.test_dir
        task.filename = 'test_perform{Root_str}.npy'
        task.mode = 'Binary file'
        task.target_array = '{Root_array}'

        task.perform()

        path = os.path.join(self.test_dir, 'test_performa.npy')
        assert_true(os.path.isfile(path))
        a = np.load(path)
        np.testing.assert_array_equal(a, task.get_from_database('Root_array'))


@attr('ui')
class TestSaveView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SaveTask(task_name='Test')
        self.root.children_task.append(self.task)

    def teardown(self):
        close_all_windows()

        self.workbench.unregister(u'hqc_meas.task_manager')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_view(self):
        # Intantiate a view with no selected interface and select one after
        window = enaml.widgets.api.Window()
        view = SaveView(window, task=self.task)
        window.show()

        process_app_events()


@attr('ui')
class TestSaveFileView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SaveFileTask(task_name='Test')
        self.root.children_task.append(self.task)

    def teardown(self):
        close_all_windows()

        self.workbench.unregister(u'hqc_meas.task_manager')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_view(self):
        # Intantiate a view with no selected interface and select one after
        window = enaml.widgets.api.Window()
        view = SaveFileView(window, task=self.task)
        window.show()

        process_app_events()


@attr('ui')
class TestSaveArrayView(object):

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(TaskManagerManifest())

        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SaveArrayTask(task_name='Test')
        self.root.children_task.append(self.task)

    def teardown(self):
        close_all_windows()

        self.workbench.unregister(u'hqc_meas.task_manager')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_view(self):
        # Intantiate a view with no selected interface and select one after
        window = enaml.widgets.api.Window()
        view = SaveArrayView(window, task=self.task)
        window.show()

        process_app_events()
