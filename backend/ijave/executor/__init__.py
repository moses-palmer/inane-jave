import asyncio
import functools
import time

from contextlib import contextmanager
from enum import Enum
from queue import Queue
from threading import Thread
from typing import TypeVar, Callable, Optional


class State(Enum):
    #: The executor has not yet been started.
    IDLE = -1

    #: The executor is running, but currently not executing a scheduled task.
    RUNNING = 0

    #: The executor is stopping.
    STOPPING = 2

    #: The executor has stopped.
    STOPPED = 3


class ToJSON:
    """An interface for types that can be converted to JSON.
    """
    def to_json(self) -> dict:
        raise NotImplementedError()


class Executor(Thread):
    #: The type of task handled by this executor.
    Task = TypeVar('Task')

    #: The result of an executed task.
    Result = TypeVar('T', bound=ToJSON)

    def __init__(
            self,
            executor: Callable[[Task], Result],
            on_complete: Callable[[Task, Result], None],
            on_error: Callable[[Task, Exception], None]):
        """A background executor.

        By calling :meth:`schedule`, a task is submitted and performed in a
        separate thread. When the task has completed, ``on_complete`` is called
        with the task and the result. If an error occurs, ``on_error`` is
        called with the task and the uncaught exception.

        :param executor: The task executor.

        :param on_complete: The completion function.

        :param on_error: The error function.
        """
        super().__init__(daemon=True)
        self._queue = Queue()
        self._executor = executor
        self._on_complete = on_complete
        self._on_error = on_error
        self._state = State.IDLE
        self._task = None

    def schedule(self, task: Task):
        """Schedules a task to be executed.

        When the task has been completed, the callable passed as
        ``on_complete`` to the constructor will be called with its result as
        its argument.

        :param task: The task to schedule.
        """
        self._queue.put(task)

    def run(self):
        self._state = State.RUNNING
        while self._state == State.RUNNING:
            task = self._queue.get()
            if task is not None:
                self._task = task
                try:
                    result = self._executor(task)
                    self._on_complete(task, result)
                except Exception as e:
                    self._on_error(task, e)
                finally:
                    self._task = None
        self._state = State.STOPPED

    def stop(self):
        """Stops the executor.

        This call is blocking until the currently executing task completes.
        """
        self._state = State.STOPPING
        self._queue.put(None)
        self.join()

    @property
    def state(self) -> State:
        """The current state of this executor.
        """
        return self._state

    @property
    def task(self) -> Task:
        """The currently executing task.
        """
        return self._task


def sync(f):
    """Turns an asynchronous function into a synchronous one.

    :param f: The asynchronous function to modify.

    :return: a synchronous function
    """
    @functools.wraps(f)
    def inner(*args, **kwargs):
        asyncio.run(f(*args, **kwargs))

    return inner


@contextmanager
def timer() -> Callable[[], Optional[time.time]]:
    """Constructs a simple timer as a context manager.
    """
    def inner():
        if end_time is not None:
            return end_time - start_time
        else:
            return None

    start_time = time.time()
    end_time = None
    yield inner
    end_time = time.time()
