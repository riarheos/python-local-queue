import logging
from dataclasses import dataclass
from threading import Condition, Thread
from typing import Callable


@dataclass
class WorkerItem:
    """
    The WorkerItem is just a placeholder for the work and it's arguments
    """
    work: Callable[..., None]
    args: tuple
    kwargs: dict


class LocalQueue:
    """
    LocalQueue implements the multithreaded runner for work. Work items may supply more work
    in the process and the run() method waits for everything to complete.

    See the usage example in README.md
    """

    def __init__(self, worker_count: int):
        self._log = logging.getLogger(self.__class__.__name__)
        self._worker_count = worker_count

        self._cond = Condition()

        self._work: list[WorkerItem] = []
        self._running = True
        self._in_progress = 0
        self._workers: list[Thread] = []
        self._error = None

    def add_work(self, work: Callable, *args, **kwargs) -> None:
        """
        Adds work to the queue. Can be run from within a work.
        """
        self._cond.acquire()
        self._work.append(WorkerItem(work, args, kwargs))
        self._cond.notify()
        self._cond.release()

    def run(self) -> None:
        """
        Runs the queue and awaits for completion. Will raise an exception if it was
        raised in a thread.
        """

        if self._worker_count <= 0:
            raise RuntimeError('Worker count must be greater than 0')

        if not self._work:
            return

        # Run workers
        self._workers = [Thread(target=self._thread) for _ in range(self._worker_count)]
        for worker in self._workers:
            worker.start()

        # Wait for the workers to do all the work
        self._cond.acquire()
        while (self._work or self._in_progress > 0) and self._running:
            self._cond.notify()
            self._cond.wait()

        # Work done, finalize and join
        self._cond.release()
        self._log.debug('No more work, finalizing')
        self.stop()

        for worker in self._workers:
            worker.join()

        self._log.debug('All done')

        if self._error:
            raise self._error

    def stop(self) -> None:
        """
        Marks the queue as stopped. Work may be skipped after this
        :return:
        """
        with self._cond:
            self._running = False
            self._cond.notify_all()

    def _thread(self) -> None:
        """
        The thread runner
        """
        self._log.debug("Worker started")
        while True:
            self._cond.acquire()

            while self._running and not self._work:
                self._cond.wait()

            if not self._running:
                self._log.debug("Exiting worker thread")
                self._cond.release()
                return

            if self._work:
                work = self._work.pop(0)
                self._in_progress += 1

                self._cond.notify()
                self._cond.release()

                try:
                    work.work(self, *work.args, **work.kwargs)
                    with self._cond:
                        self._in_progress -= 1
                        self._cond.notify_all()
                except Exception as e:
                    self._error = e
                    self._log.exception("Exception while running work")
                    self.stop()
