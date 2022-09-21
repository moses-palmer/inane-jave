from . import db


def main(database: db.Database):
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


if __name__ == '__main__':
    import argparse
    import logging

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        prog='ijave',
        description='Launches the Inane Jave server.')

    parser.add_argument(
        'database',
        help='the database file backing the application',
        type=db.Database)

    main(**vars(parser.parse_args()))
