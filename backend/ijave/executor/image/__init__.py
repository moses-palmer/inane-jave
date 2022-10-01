import logging
import multiprocessing as mp

from dataclasses import dataclass

from ... import db, ent, message
from .. import Executor, sync


LOG = logging.getLogger(__name__)

#: The kind of messages generated.
KIND = 'project'

#: The granularity of image dimensions.
GRANULARITY = 128


@dataclass
class Task:
    """A task executed by this generator.
    """
    #: The prompt for which to generate an image.
    prompt: ent.Prompt

    #: The image width.
    width: int

    #: The image height.
    height: int

    #: The random seed used to generate the first image.
    seed: int

    def to_json(self) -> dict:
        return {
            'prompt': self.prompt.to_json(),
            'width': self.width,
            'height': self.height,
            'seed': self.seed}


@dataclass
class Result:
    """The results broadcast.
    """
    #: The prompt containing the image.
    prompt: ent.Prompt

    #: The ID of the image generated.
    image: ent.ImageID

    #: The progress.
    progress: float

    def to_json(self) -> dict:
        return {
            'prompt': self.prompt.to_json(),
            'image': str(self.image),
            'progress': self.progress}


@dataclass
class Input:
    #: The task to execute.
    task: Task

    #: The cached data.
    cached: ent.ImageExecutorCache


@dataclass
class Output:
    #: The task that was executed.
    task: Task

    #: Updated cached data.
    cached: ent.ImageExecutorCache

    #: The image content type.
    content_type: str

    #: An encoded image.
    image_data: bytes


def normalize(i: int) -> int:
    """Normalises a dimension value to the granularity.

    :param i: The value to normalise.
    :return: a normalised value
    """
    return round(i // GRANULARITY) * GRANULARITY


def executor(
        database: db.Database,
        broker: message.Broker) -> Executor:
    """Generates an executor for images.

    When an image has been generated, it is sent on the topic
    ``(KIND, project_id)``.

    :param database: The application database.

    :param broker: A message broker.
    """
    def remote_executor(pipe):
        from . import remote

        generator = remote.Generator()

        while True:
            try:
                command = pipe.recv()
                result = generator.generate(command)
                pipe.send(result)
            except EOFError:
                LOG.info('Remote executor shutting down')
                return

    (local_pipe, remote_pipe) = mp.Pipe()
    process = mp.Process(target=remote_executor, args=(remote_pipe,))
    process.start()

    def execute(task: Task) -> Result:
        with database.transaction() as tx:
            cached = database.load(
                tx,
                ent.ImageExecutorCacheID.from_prompt_id(task.prompt.id))
        if cached.step >= cached.steps:
            LOG.info(
                'Received request to execute task %s, but it has completed',
                task)
            return

        local_pipe.send(Input(
            task=task,
            cached=cached))
        r = local_pipe.recv()

        with database.transaction() as tx:
            # Update the state
            database.update(tx, r.cached)

            # Store the image and link it to the prompt
            entity = ent.Image(
                id=ent.ImageID.new(),
                timestamp=database.now(),
                content_type=r.content_type,
                data=r.image_data)
            database.create(tx, entity)
            database.link(tx, r.task.prompt, entity)

            return Result(
                prompt=r.task.prompt,
                image=entity.id,
                progress=(r.cached.step + 1) / r.cached.steps)

    @sync
    async def on_complete(task: Task, result: Result):
        topic = message.Topic(
            kind=KIND,
            name=task.prompt.project)
        broadcaster = await broker.broadcaster(topic)
        await broadcaster.send(result)

    def on_error(task: Task, error: Exception):
        LOG.exception('Failed to generate an image for {}'.format(task))

    return Executor(
        execute,
        on_complete,
        on_error)
