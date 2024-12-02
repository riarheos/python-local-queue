from unittest import TestCase

import pytest

from LocalQueue import LocalQueue


@pytest.mark.timeout(1)
class TestLocalQueue(TestCase):
    def test__zero_workers(self):
        q = LocalQueue(0)
        q.add_work(lambda q: None)
        with pytest.raises(RuntimeError, match="Worker count must be greater than 0"):
            q.run()

    def test__zero_work(self):
        q = LocalQueue(1)
        q.run()

    def test__sum(self):
        q = LocalQueue(5)
        s = {'sum': 0}

        def work(q, i):
            s['sum'] += i
            for _ in range(i):
                q.add_work(work, i - 1)

        q.add_work(work, 3)
        q.run()

        # 15 == 3 + 3 * ( 2 + 2 * 1 )
        assert s['sum'] == 15

    def test__exc(self):
        q = LocalQueue(1)

        def work(_):
            raise ValueError('Foo')

        q.add_work(work)
        with pytest.raises(ValueError, match="Foo"):
            q.run()

    def test__kwargs(self):
        q = LocalQueue(1)
        s = {'sum': 0}

        def work(_, argname):
            s['sum'] += argname

        q.add_work(work, argname=100)
        q.run()

        assert s['sum'] == 100
