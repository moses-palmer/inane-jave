from aiohttp import web

from . import ALL, field, not_found
from .. import ent


#: The allowed upload content types.
ALLOWED_CONTENT_TYPES = (
    'image/jpeg',
    'image/png')


@ALL.post('/api/image')
async def create(req):
    if req.content_type != 'multipart/form-data':
        raise web.HTTPUnsupportedMediaType()

    reader = await req.multipart()
    ids = []
    with req.app.db.transaction() as tx:
        while True:
            f = await reader.next()
            if f is None:
                break
            else:
                content_type = field(f.headers, 'content-type', str)
                if content_type not in ALLOWED_CONTENT_TYPES:
                    raise web.HTTPUnsupportedMediaType()
                else:
                    entity = ent.Image(
                        id=ent.ImageID.new(),
                        timestamp=req.app.db.now(),
                        content_type=content_type,
                        data=bytes(await f.read()))
                    req.app.db.create(tx, entity)
                    ids.append(str(entity.id))
    return web.json_response(ids, status=202)


@ALL.get('/api/image/{id}/png')
async def png(req):
    try:
        id = ent.ImageID.from_string(req.match_info['id'])
    except ValueError as e:
        raise web.HTTPBadRequest(body=str(e))

    with req.app.db.transaction() as tx:
        entity = req.app.db.load(tx, id)

        if entity is not None and entity.data_is_loaded:
            return web.Response(
                body=entity.data,
                content_type=entity.content_type)
        else:
            return not_found()


@ALL.delete('/api/image/{id}')
async def delete(req):
    try:
        id = ent.ImageID.from_string(req.match_info['id'])
    except ValueError as e:
        raise web.HTTPBadRequest(body=str(e))

    with req.app.db.transaction() as tx:
        if req.app.db.delete(tx, id):
            return web.Response()
        else:
            return not_found()
