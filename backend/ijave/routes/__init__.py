"""
Route definitions
-----------------

The definitions are grouped into modules based on resource type, but ``ALL`` is
imported and populated in all submodules.
"""
from json import JSONDecodeError
from typing import get_args, get_origin, Any, Union

from aiohttp import web

from .. import ent

#: All routes.
ALL = web.RouteTableDef()


def created(entity: ent.Entity) -> web.Response:
    """Generates a *202 Created* response containing the entity.

    :param entity: The entity that was created.

    :return: a response
    """
    return web.json_response(entity.to_json(), status=202)


def not_found() -> web.Response:
    """Generates a *404 Not Found* response.

    :return: a response
    """
    return web.Response(status=404)


def field(data: dict, name: str, type: type) -> web.Response:
    """Reads the value of a field.

    :param data: The source of values.

    :param name: The name of the field.

    :param type: The expected type of the field.

    :return: a response
    """
    try:
        value = data[name] \
            if get_origin(type) is not Union else \
            data.get(name)
        return type(value) \
            if get_origin(type) is not Union else \
            get_args(type)[0](value) \
            if value is not None \
            else None
    except KeyError:
        raise web.HTTPBadRequest(
            body='missing field "{}"'.format(name))
    except TypeError:
        raise web.HTTPBadRequest(
            body='invalid value for field "{}": "{}"'.format(
                name,
                data.get(name)))


def assert_missing(data: dict, *fields) -> dict:
    """Ensures that nont of the fields passed in ``fields`` are present in
    ``data``.

    :param data: The object to check.

    :param fields: The prohibited field names.

    :raise web.HTTPBadRequest: if any of the fields are present

    :return: ``data``
    """
    if any(
            field in data
            for field in fields):
        raise web.HTTPBadRequest()
    else:
        return data


async def json(req: web.Request) -> dict:
    """Extracts a JSON payload from a request.

    :param req: The request.

    :return: the payload

    :raise web.HTTPBadRequest: if the value is invalid JSON
    """
    try:
        if req.content_type == 'application/json':
            return await req.json()
        else:
            raise web.HTTPUnsupportedMediaType()
    except JSONDecodeError:
        raise web.HTTPBadRequest()


def file_field(value: Any) -> web.FileField:
    """Converts a value to a file field.

    If the type is invalid, a *400 Bad Request* is raised.

    :param value: The value to convert.

    :return: a file field
    """
    if isinstance(value, web.FileField):
        return value
    else:
        raise web.HTTPBadRequest('invalid file upload')


# Import just to fill in routing definitions
from . import image as _
from . import prompt as _
from . import project as _
