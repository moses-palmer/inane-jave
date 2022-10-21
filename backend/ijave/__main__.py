import os
import sys

from aiohttp import web

from . import db, message, routes
from .executor.image import executor as image_executor


#: The port on which to listen.
PORT = os.getenv('IJAVE_PORT', '8080')

#: If present, a local direcory from which to serve static files.
IJAVE_STATIC_DIR = os.getenv('IJAVE_STATIC_DIR')


def main(version: str, database: db.Database, port: int):
    import logging

    logging.basicConfig(level=logging.DEBUG)

    async def on_prepare(request, response):
        response.headers['server'] = 'Inane Jave/' + version

    app = web.Application()
    app.on_response_prepare.append(on_prepare)
    app.add_routes(routes.ALL)
    app.db = database

    app.broker = message.Broker()
    app.image_executor = image_executor(app.db, app.broker)
    app.image_executor.start()

    if IJAVE_STATIC_DIR is not None:
        async def serve_index(req):
            return web.FileResponse(
                os.path.join(IJAVE_STATIC_DIR, 'index.html'))

        app.router.add_get('/', serve_index)
        app.router.add_static('/', IJAVE_STATIC_DIR)

    print('=== Starting web server ===')
    sys.stdout.flush()
    web.run_app(app, port=port)

    app.image_executor.stop()


if __name__ == '__main__':
    import argparse
    import logging

    logging.basicConfig(level=logging.INFO)

    with open(
            os.path.join(
                os.path.dirname(__file__),
                os.path.pardir,
                'VERSION'),
            encoding='utf-8') as f:
        version = f.read().strip()

    parser = argparse.ArgumentParser(
        prog='ijave',
        description='Launches the Inane Jave server.')

    parser.add_argument(
        'database',
        help='the database file backing the application',
        type=db.Database)

    try:
        port = int(PORT)
    except ValueError:
        sys.stderr.write(
            'Please set set $IJAVE_PORT to a number in the range 1024 - '
            '65535.\n')
        sys.exit(1)
    else:
        main(version, port=port, **vars(parser.parse_args()))
