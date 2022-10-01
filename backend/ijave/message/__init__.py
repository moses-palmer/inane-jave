from asyncio import Lock, Queue, create_task, wait_for, wait
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True, eq=True)
class Topic:
    """A message topic.
    """
    #: The kind of messages sent.
    kind: str

    #: The topic name.
    name: str


class Listener:
    """A listener on a topic.

    This class is an asynchronous iterator over messages on the topic.
    """
    def __init__(self, parent):
        self._active = True
        self._queue = Queue()
        self._parent = parent

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self.receive()

    async def receive(self, timeout: Optional[float] = None) -> Any:
        """Receives the next message.

        :param timeout: A timeout.
        """
        if self._active:
            if timeout is not None:
                return await wait_for(self._queue.get(), timeout=timeout)
            else:
                return await self._queue.get()
        else:
            return None

    async def stop(self):
        """Stops receiving messages.

        Once this method has been called, no more messages can be received.
        """
        await self._parent._unregister(self)
        self._active = False


class Broadcaster:
    """A message broadcaster.

    This class asynchronously sends messages to zero or more listeners.
    """
    def __init__(self, topic: Topic):
        self._lock = Lock()
        self._topic = topic
        self._listeners = []

    async def send(self, message: Any):
        """Broadcasts a single message to all listeners.

        :param message: The message to send.
        """
        async with self._lock:
            if len(self._listeners) > 0:
                await wait([
                    create_task(listener._queue.put(message))
                    for listener in self._listeners])

    async def _register(self, listener: Listener):
        """Registers a new listener.

        :param listener: The listener to register.
        """
        async with self._lock:
            self._listeners.append(listener)

    async def _unregister(self, listener: Listener):
        """Unregisters a listener.

        :param listener: The listener to unregister.

        :raise ValueError: if the listener is not registered
        """
        async with self._lock:
            self._listeners.remove(listener)


class Broker:
    """A message broker.
    """
    def __init__(self):
        self._lock = Lock()
        self._topics = {}

    async def broadcaster(self, topic: Topic) -> Broadcaster:
        """Generates a broadcaster for a specific topic.

        :param topic: The topic for the broadcaster.

        :return: a broadcaster
        """
        async with self._lock:
            if topic not in self._topics:
                self._topics[topic] = Broadcaster(topic)
            return self._topics[topic]

    async def listener(self, topic: Topic) -> Listener:
        """Generates a listener for a specific topic.

        :param topic: The topic for the listener.

        :return: a listener
        """
        broadcaster = await self.broadcaster(topic)
        result = Listener(broadcaster)
        await broadcaster._register(result)
        return result
