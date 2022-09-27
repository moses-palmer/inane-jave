from aiohttp import web

from . import ALL, created, not_found
from .. import ent


@ALL.get('/api/prompt/{id}')
async def get(req):
    try:
        id = ent.PromptID.from_string(req.match_info['id'])
    except ValueError as e:
        raise web.HTTPBadRequest(body=str(e))

    with req.app.db.transaction() as tx:
        entity = req.app.db.load(tx, id)

        if entity is not None:
            return web.json_response(entity.to_json())
        else:
            return not_found()


@ALL.delete('/api/prompt/{id}')
async def delete(req):
    try:
        id = ent.PromptID.from_string(req.match_info['id'])
    except ValueError as e:
        raise web.HTTPBadRequest(body=str(e))

    with req.app.db.transaction() as tx:
        if req.app.db.delete(tx, id):
            return web.Response()
        else:
            return not_found()


@ALL.get('/api/prompt/{id}/icon')
async def icon(req):
    try:
        id = ent.PromptID.from_string(req.match_info['id'])
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


@ALL.get('/api/prompt/{id}/images')
async def images(req):
    try:
        id = ent.PromptID.from_string(req.match_info['id'])
    except ValueError as e:
        raise web.HTTPBadRequest(body=str(e))

    return web.json_response(
        [
            image.to_json()
            for image in req.app.db.images(id)])
