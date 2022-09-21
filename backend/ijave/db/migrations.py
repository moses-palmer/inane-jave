"""
Database migrations
-------------------

This module provides functionality to manage database migrations.

A table, ``Migrations`` is maintained to keep track of the current schema
version. Available versions are specified by files in the directory
``./migrations/``.

A version consists of a file with a name on the format
``<version>-<some-description>.sql``. The ``version`` field must be an integer
increasing by one for each upgrade. If a function named after the migration
description, with ``'-'`` replaced by ``'_'``, and with the suffix ``'_pre'``,
exists in this module, it is executed before the SQL commands are executed, and
if a similarly named function, with suffix ``'_post'`` exists, it will be
executed after.
"""
import logging
import os
import sqlite3

from typing import List

LOG = logging.getLogger(__name__)


def apply(conn: sqlite3.Connection):
    """Applies migrations to a database.

    :param conn: The database connection.
    """
    from . import transaction
    current = _current(conn)
    migrations_dir = _migrations_dir()
    migrations = _migrations(migrations_dir)

    for i in range(current, len(migrations)):
        version = i + 1
        name = migrations[i]
        migration = os.path.join(migrations_dir, name)
        identifier = '_'.join(name.split('-')[1:])
        assert int(name.split('-', 1)[0], 10) == version

        try:
            with transaction(conn) as tx:
                globals().get('{}_pre'.format(identifier), lambda _: None)(tx)
                with open(migration, encoding='utf-8') as f:
                    tx.executescript(f.read())
                globals().get('{}_post'.format(identifier), lambda _: None)(tx)
                conn.execute('INSERT INTO Migrations VALUES(?)', (version, ))
        except Exception as e:
            LOG.error('Failed to apply migration %s', name, exc=e)
            raise


def _migrations_dir() -> str:
    """The directory containing migrations.

    :return: a path
    """
    return os.path.join(
        os.path.dirname(__file__),
        'migrations')


def _migrations(root: str) -> List[str]:
    """Returns a list of migration files.

    A migration file has a name on the format ``<number>-<description>.sql``.

    :return: a list of names
    :raise ValueError: if ``root`` contains a file ending with ``.sql`` that
        has an invalid format
    """
    return list(sorted(
        (
            name
            for name in os.listdir(root)
            if name.endswith('.sql')),
        key=lambda name: int(name.split('-', 1)[0], 10)))


def _current(conn) -> int:
    """Determines the current database version.

    :param conn: The database connection.

    :return: the current version, or ``0` if no versions have been applied

    """
    try:
        res = conn \
                .execute('SELECT MAX(version) FROM Migrations') \
                .fetchone()
        return res[0]
    except sqlite3.OperationalError:
        return 0
