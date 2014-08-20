# -*- coding: utf-8 -*-
# =============================================================================
# module : test_execution.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from hqc_meas.tasks.api import RootTask
from nose.tools import assert_true, assert_false
from multiprocessing import Event
from threading import Thread
from time import sleep

from ..util import complete_line
from.testing_utilities import CheckTask, ExceptionTask


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


class TestTaskExecution(object):

    def setup(self):
        root = RootTask()
        root.should_pause = Event()
        root.should_stop = Event()
        root.paused = Event()
        root.default_path = 'toto'
        self.root = root

    def test_root_perform1(self):
        # Test running an empty RootTask.
        root = self.root
        root.perform()

        assert_false(root.should_pause.is_set())
        assert_false(root.should_stop.is_set())

    def test_root_perform2(self):
        # Test handling a child raising an exception.
        root = self.root
        root.children_task.append(ExceptionTask())

        root.perform()

        assert_false(root.should_pause.is_set())
        assert_true(root.should_stop.is_set())

    def test_root_perform3(self):
        # Test running a simple task.
        root = self.root
        aux = CheckTask(task_name='test')
        root.children_task.append(aux)

        root.perform()

        assert_false(root.should_pause.is_set())
        assert_false(root.should_stop.is_set())
        assert_true(aux.perform_called)

    def test_root_perform4(self):
        # Test running a simple task in parallel.
        root = self.root
        aux = CheckTask(task_name='test')
        aux.parallel = {'activated': True, 'pool': 'test'}
        root.children_task.append(aux)
        root.children_task.append(CheckTask())

        root.perform()

        assert_false(root.should_pause.is_set())
        assert_false(root.should_stop.is_set())
        assert_true(aux.perform_called)

    def test_root_perform5(self):
        # Test running a simple task waiting on all pools.
        root = self.root
        par = CheckTask(task_name='test', time=0.1)
        par.parallel = {'activated': True, 'pool': 'test'}
        aux = CheckTask(task_name='wait')
        aux.wait = {'activated': True}
        root.children_task.extend([par, aux])

        root.perform()

        assert_false(root.should_pause.is_set())
        assert_false(root.should_stop.is_set())
        assert_true(aux.perform_called)
        assert_false(root.threads['test'])

    def test_root_perform6(self):
        # Test running a simple task waiting on a single pool.
        root = self.root
        par = CheckTask(task_name='test', time=0.1)
        par.parallel = {'activated': True, 'pool': 'test'}
        par2 = CheckTask(task_name='test2', time=0.1)
        par2.parallel = {'activated': True, 'pool': 'aux'}
        aux = CheckTask(task_name='test')
        aux.wait = {'activated': True, 'wait': ['test']}
        root.children_task.extend([par, par2, aux])

        root.perform()

        assert_false(root.should_pause.is_set())
        assert_false(root.should_stop.is_set())
        assert_true(aux.perform_called)
        assert_false(root.threads['test'])
        assert_true(root.threads['aux'])

    def test_root_perform7(self):
        # Test running a simple task not waiting on a single pool.
        root = self.root
        par = CheckTask(task_name='test', time=0.1)
        par.parallel = {'activated': True, 'pool': 'test'}
        par2 = CheckTask(task_name='test2', time=0.1)
        par2.parallel = {'activated': True, 'pool': 'aux'}
        aux = CheckTask(task_name='test')
        aux.wait = {'activated': True, 'no_wait': ['aux']}
        root.children_task.extend([par, par2, aux])

        root.perform()

        assert_false(root.should_pause.is_set())
        assert_false(root.should_stop.is_set())
        assert_true(aux.perform_called)
        assert_false(root.threads['test'])
        assert_true(root.threads['aux'])

    def test_stop(self):
        # Test stopping the execution.
        root = self.root
        par = CheckTask(task_name='test', time=0.1)
        par2 = CheckTask(task_name='test2', time=0.1)
        root.children_task.extend([par, par2])

        t = Thread(target=root.perform)
        t.start()
        sleep(0.01)
        root.should_stop.set()

        assert_true(par.perform_called)
        assert_false(par2.perform_called)

    def test_pause1(self):
        # Test pausing and resuming the execution.
        # Tricky as only the main thread is allowed to resume.
        root = self.root
        par = CheckTask(task_name='test', time=1.0)
        par2 = CheckTask(task_name='test2', time=0.1)
        root.children_task.extend([par, par2])

        def aux(root):
            root.should_pause.set()
            root.paused.wait()
            root.should_pause.clear()

        t = Thread(target=aux, args=(root,))
        t.start()
        root.perform()
        t.join()

        assert_false(root.should_pause.is_set())
        assert_false(root.should_stop.is_set())
        assert_true(par.perform_called)
        assert_true(par2.perform_called)
        assert_true(root.resume.is_set())

    def test_pause2(self):
        # Test pausing and stopping the execution.
        root = self.root
        par = CheckTask(task_name='test', time=1.0)
        par2 = CheckTask(task_name='test2', time=0.1)
        root.children_task.extend([par, par2])

        t = Thread(target=root.perform)
        t.start()
        sleep(0.01)
        root.should_pause.set()
        root.paused.wait()
        root.should_stop.set()
        t.join()

        assert_true(root.should_pause.is_set())
        assert_true(root.should_stop.is_set())
        assert_true(par.perform_called)
        assert_false(par2.perform_called)
