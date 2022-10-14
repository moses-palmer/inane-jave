from aiohttp import web

from . import ALL, image_redirect, not_found
from .. import ent
from ..executor import image


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
        image_id = req.app.db.icon(tx, id)
        if image_id is not None:
            return image_redirect(image_id)
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


@ALL.post('/api/prompt/{id}/generate-next')
async def image_generate(req):
    try:
        id = ent.PromptID.from_string(req.match_info['id'])
    except ValueError as e:
        raise web.HTTPBadRequest(body=str(e))

    with req.app.db.transaction() as tx:
        prompt = req.app.db.load(tx, id)
        if prompt is None:
            return not_found()
        cached = req.app.db.load(
            tx,
            ent.ImageExecutorCacheID.from_prompt_id(id))
        if cached.step >= cached.steps:
            return web.Response(status=202)
        project = req.app.db.load(tx, prompt.project)

    req.app.image_executor.schedule(image.Task(
        prompt=prompt,
        width=project.image_width,
        height=project.image_height,
        seed=None))

    return web.Response(status=202)
