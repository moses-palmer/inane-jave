from aiohttp import web

from . import ALL, created, assert_missing, field, json, not_found
from .. import ent


@ALL.post('/api/project')
async def create(req):
    data = await json(req)

    entity = ent.Project(
        id=ent.ProjectID.new(),
        name=field(data, 'name', str),
        description=field(data, 'description', str))
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
        entity = req.app.db.icon(tx, id)
        if entity is not None and entity.data_is_loaded:
            return web.Response(
                body=entity.data,
                content_type=entity.content_type)
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
            entity = ent.Prompt(
                id=ent.PromptID.new(),
                project=project.id,
                text=field(data, 'text', str))
            req.app.db.create(tx, entity)
            return created(entity)
        else:
            return not_found()
