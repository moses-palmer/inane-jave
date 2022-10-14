from asyncio import TimeoutError

from aiohttp import web

from . import (
    ALL,
    PING_INTERVAL,
    created,
    assert_missing,
    field,
    image_redirect,
    json,
    not_found)
from .. import ent
from ..executor import image
from ..message import Topic


@ALL.post('/api/project')
async def create(req):
    data = await json(req)

    entity = ent.Project(
        id=ent.ProjectID.new(),
        name=field(data, 'name', str),
        description=field(data, 'description', str),
        image_width=field(data, 'image_width', image.normalize),
        image_height=field(data, 'image_height', image.normalize))
    with req.app.db.transaction() as tx:
        req.app.db.create(tx, entity)
    return created(entity)


@ALL.get('/api/project/{id}')
async def get(req):
    try:
        id = ent.ProjectID.from_string(req.match_info['id'])
    except ValueError as e:
        raise web.HTTPBadRequest(body=str(e))

    with req.app.db.transaction() as tx:
        entity = req.app.db.load(tx, id)

        if entity is not None:
            return web.json_response(entity.to_json())
        else:
            return not_found()


@ALL.put('/api/project/{id}')
async def update(req):
    data = assert_missing(await json(req), 'id')
    try:
        id = ent.ProjectID.from_string(req.match_info['id'])
    except ValueError as e:
        raise web.HTTPBadRequest(body=str(e))

    with req.app.db.transaction() as tx:
        entity = req.app.db.load(tx, id)

        if entity is not None:
            try:
                for (key, value) in data.items():
                    setattr(entity, key, value)
                entity = entity.validate_fields()
                req.app.db.update(tx, entity)
                return web.json_response(entity.to_json())
            except ValueError as e:
                raise web.HTTPBadRequest(body='invalid field: "{}"'.format(e))
        else:
            return not_found()


@ALL.delete('/api/project/{id}')
async def delete(req):
    try:
        id = ent.ProjectID.from_string(req.match_info['id'])
    except ValueError as e:
        raise web.HTTPBadRequest(body=str(e))

    with req.app.db.transaction() as tx:
        if req.app.db.delete(tx, id):
            return web.Response()
        else:
            return not_found()


@ALL.get('/api/project/{id}/icon')
async def icon(req):
    try:
        id = ent.ProjectID.from_string(req.match_info['id'])
    except ValueError as e:
        raise web.HTTPBadRequest(body=str(e))

    with req.app.db.transaction() as tx:
        icon_id = req.app.db.icon(tx, id)
        if icon_id is not None:
            print('PROJECT', icon_id)
            return image_redirect(icon_id)
        else:
            return not_found()


@ALL.get('/api/project')
async def all_entities(req):
    return web.json_response(
        [
            project.to_json()
            for project in req.app.db.projects()])


@ALL.get('/api/project/{id}/prompts')
async def prompts(req):
    try:
        id = ent.ProjectID.from_string(req.match_info['id'])
    except ValueError as e:
        raise web.HTTPBadRequest(body=str(e))

    with req.app.db.transaction() as tx:
        project = req.app.db.load(tx, id)

        if project is not None:
            return web.json_response(
                [
                    prompt.to_json()
                    for prompt in req.app.db.prompts(project.id)])
        else:
            return not_found()


@ALL.post('/api/project/{id}/prompts')
async def prompt_create(req):
    try:
        id = ent.ProjectID.from_string(req.match_info['id'])
    except ValueError as e:
        raise web.HTTPBadRequest(body=str(e))

    with req.app.db.transaction() as tx:
        project = req.app.db.load(tx, id)

        if project is not None:
            data = await json(req)
            if isinstance(data.get('seed'), float):
                seed = int(field(data, 'seed', float))
            else:
                seed = None
            entity = ent.Prompt(
                id=ent.PromptID.new(),
                project=project.id,
                text=field(data, 'text', str))
            req.app.db.create(tx, entity)
            cached = ent.ImageExecutorCache(
                id=ent.ImageExecutorCacheID.from_prompt_id(entity.id),
                step=0,
                steps=field(data, 'steps', int),
                strength=field(data, 'strength', float),
                latent=None)
            req.app.db.create(tx, cached)
            req.app.image_executor.schedule(image.Task(
                prompt=entity,
                width=project.image_width,
                height=project.image_height,
                seed=seed))
            return created(entity)
        else:
            return not_found()


@ALL.get('/api/project/{id}/notifications')
async def notifications(req):
    id = ent.ProjectID.from_string(req.match_info['id'])

    broker = req.app.broker

    async def image_data() -> dict:
        try:
            data = await image_data.listener.receive(timeout=PING_INTERVAL)
            if data is None:
                raise InterruptedError()
            kind = 'completed'
        except (TimeoutError, InterruptedError):
            data = image_data.executor.task
            if data is not None:
                kind = 'running'
            else:
                kind = 'idle'
        return {
            'kind': kind,
            'data': data.to_json() if data is not None else None}
    image_data.executor = req.app.image_executor
    image_data.listener = await broker.listener(Topic(image.KIND, id))

    with req.app.db.transaction() as tx:
        project = req.app.db.load(tx, id)
    if project is not None:
        ws = web.WebSocketResponse()
        await ws.prepare(req)

        while True:
            try:
                await ws.send_json({
                    'image': await image_data()})
            except (ConnectionResetError, RuntimeError):
                # Connection possibly closed
                break

        await image_data.listener.stop()

        return ws
    else:
        return not_found()
