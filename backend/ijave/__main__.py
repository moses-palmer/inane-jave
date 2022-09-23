import os
import sys

from aiohttp import web

from . import db, routes


#: The port on which to listen.
PORT = os.getenv('IJAVE_PORT', '8080')


def main(version: str, database: db.Database, port: int):
    import logging

    logging.basicConfig(level=logging.DEBUG)

    print('Projects:')
    for project in database.projects():
        print('  - id: {}'.format(project.id))
        print('    name: {}'.format(project.name))
        print('    description: {}'.format(project.description))
        print('    prompts:')
        for prompt in database.prompts(project.id):
            print('    - id: {}'.format(prompt.id))
            print('      text: {}'.format(prompt.text))
            print('      images:')
            for image in database.images(prompt.id):
                print('      - id: {}'.format(image.id))
                print('        timestamp: {}'.format(image.timestamp))

    async def on_prepare(request, response):
        response.headers['server'] = 'Inane Jave/' + version

    app = web.Application()
    app.on_response_prepare.append(on_prepare)
    app.add_routes(routes.ALL)
    app.db = database

    print('=== Starting web server ===')
    sys.stdout.flush()
    web.run_app(app, port=port)


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
