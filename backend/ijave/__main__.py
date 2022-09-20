def main(database: str):
    print('TODO: Implement!')


if __name__ == '__main__':
    import argparse
    import logging

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        prog='ijave',
        description='Launches the Inane Jave server.')

    parser.add_argument(
        'database',
        help='the database file backing the application')

    main(**vars(parser.parse_args()))
