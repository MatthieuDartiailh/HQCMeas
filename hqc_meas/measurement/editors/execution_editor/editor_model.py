# -*- coding: utf-8 -*-
# =============================================================================
# module : editor.enaml
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from atom.api import Atom, Value, Typed, List
from collections import Counter

from hqc_meas.tasks.api import ComplexTask


class _Model(Atom):
    """ Model for the execution editor.

    Walk all the tasks to determine which pool of tasks are defined and keep a
    counter.

    """
    root = Value()

    pools = List()

    def bind_observers(self):
        """

        """
        counter = Counter()
        self._bind_observers(self.root, counter)

        self._counter = counter
        self.pools = list(set(counter.elements()))

    def unbind_observers(self):
        """

        """
        self._unbind_observers(self.root, Counter())

    # --- Private API ---------------------------------------------------------

    _counter = Typed(Counter, ())

    def _bind_observers(self, task, counter):
        """

        """
        if isinstance(task, ComplexTask):
            task.observe('children_task', self._children_observer)
            for child in task._gather_children_task():
                self._bind_observers(child, counter)

        else:
            pools = []
            parallel = task.parallel
            if parallel.get('activated'):
                pool = parallel['pool']
                if pool:
                    pools.append(pool)

            wait = task.wait
            if wait.get('activated'):
                pools.extend(wait.get('wait', []))
                pools.extend(wait.get('no_wait', []))

            counter.update(pools)

            task.observe('parallel', self._task_observer)
            task.observe('wait', self._task_observer)

    def _unbind_observers(self, task, counter):
        """

        """
        if isinstance(task, ComplexTask):
            task.unobserve('children_task', self._children_observer)
            for child in task._gather_children_task():
                self._unbind_observers(child, counter)

        else:
            pools = []
            parallel = task.parallel
            if parallel.get('activated'):
                pool = parallel['pool']
                if pool:
                    pools.append(pool)

            wait = task.wait
            if wait.get('activated'):
                pools.extend(wait.get('wait', []))
                pools.extend(wait.get('no_wait', []))

            counter.subtract(pools)

            task.unobserve('parallel', self._task_observer)
            task.unobserve('wait', self._task_observer)

    def _observe_root(self, change):
        """

        """
        if 'oldvalue' in change and change['oldvalue']:
            self.unbind_observers(change['oldvalue'])

        root = change['value']
        if root:
            self.bind_observers()

    def _task_observer(self, change):
        """

        """
        if change['name'] == 'parallel':
            activated = change['value'].get('activated')
            pool = change['value'].get('pool')
            if not activated and pool:
                self._counter[pool] -= 1
                self.pools = list(set(self._counter.elements()))

            elif activated and pool:
                self._counter[pool] += 1
                self.pools = list(set(self._counter.elements()))

        else:
            activated = change['value'].get('activated')
            wait = change['value'].get('wait', [])
            no_wait = change['value'].get('no_wait', [])
            counter = Counter(wait + no_wait)

            if not activated and counter:
                self._counter.substract(counter)
                self.pools = list(set(self._counter.elements()))

            elif activated and counter:
                self._counter.update(counter)
                self.pools = list(set(self._counter.elements()))

    def _children_observer(self, change):
        """

        """
        added = set(change['value']) - set(change.get('oldvalue', []))
        removed = set(change.get('oldvalue', [])) - set(change['value'])

        counter = Counter()

        for child in removed:
            self._unbind_observers(child, counter)

        for child in added:
            self._bind_observers(child, counter)

        self._counter.update(counter)
        self.pools = list(set(counter.elements()))
