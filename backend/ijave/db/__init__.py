"""
Database helpers
----------------

This module provides a simple helper to access typed data from the database
handle database migrations.
"""

import logging
import sqlite3

from contextlib import contextmanager
from datetime import datetime
from threading import RLock
from typing import Generator, Optional, Sequence

from .. import ent
from . import migrations


Cur = sqlite3.Cursor

LOG = logging.getLogger(__name__)


@contextmanager
def transaction(conn: sqlite3.Connection) -> Generator[
        sqlite3.Cursor, None, None]:
    """Opens a transaction to the database and provides a cursor as a context
    manager.

    :param conn: An existing database connection.

    :return: an active transaction
    """
    cur = conn.cursor()
    cur.execute('BEGIN TRANSACTION')
    try:
        yield cur
    except Exception as e:
        LOG.error(
            'ROLLBACK because of uncaught exception: %s',
            e)
        conn.rollback()
        raise
    else:
        conn.commit()
    finally:
        cur.close()


class Database:
    def __init__(self, database):
        """A class providing typed access to the database.

        :param data: The database connection string.
        """
        self._lock = RLock()
        self._conn = sqlite3.connect(
            database,
            isolation_level=None,
            check_same_thread=False)
        migrations.apply(self._conn)

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Cursor, None, None]:
        """Opens a transaction to the database and provides a cursor as a
        context manager.

        :return: an active transaction
        """
        with self._lock:
            cur = self._conn.cursor()
            cur.execute('BEGIN TRANSACTION')
            try:
                yield cur
            except Exception as e:
                LOG.error(
                    'ROLLBACK because of uncaught exception: %s',
                    e)
                self._conn.rollback()
                raise
            else:
                self._conn.commit()
            finally:
                cur.close()

    def create(self, tx: sqlite3.Cursor, entity: ent.Entity):
        """Creates an entity in the database.

        The entity may not already exist.

        :param tx: An ongoing transaction.

        :param entity: The entity to create.

        :raise ValueError: if the entity type is not supported
        """
        if isinstance(entity, ent.Project):
            tx.execute('''
                INSERT INTO Project(id, name, description)
                VALUES(?, ?, ?)''', (
                    entity.id,
                    entity.name,
                    entity.description))
        elif isinstance(entity, ent.Prompt):
            tx.execute('''
                INSERT INTO Prompt(id, project, text)
                VALUES(?, ?, ?)''', (
                    entity.id,
                    entity.project,
                    entity.text))
        elif isinstance(entity, ent.Image):
            tx.execute('''
                INSERT INTO Image(id, timestamp, content_type, data)
                VALUES(?, ?, ?, ?)''', (
                    entity.id,
                    entity.timestamp,
                    entity.content_type,
                    entity.data))
        else:
            raise ValueError(entity)

    def load(self, tx: sqlite3.Cursor, id: ent.ID) -> Optional[ent.Entity]:
        """Loads an entity from the database.

        :param tx: An ongoing transaction.

        :param id: The ID of the entity to load.

        :raise ValueError: if the entity ID type is not supported
        """
        if isinstance(id, ent.ProjectID):
            tx.execute(
                    '''
                    SELECT name, description
                    FROM Project
                    WHERE id = ?''', (
                        id,))
            r = tx.fetchone()
            if r is not None:
                (name, description) = r
                return ent.Project(
                    id=id,
                    name=name,
                    description=description)
        elif isinstance(id, ent.PromptID):
            tx.execute(
                    '''
                    SELECT project, text
                    FROM Prompt
                    WHERE id = ?''', (
                        id,))
            r = tx.fetchone()
            if r is not None:
                (project, text) = r
                return ent.Prompt(
                    id=id,
                    project=ent.ProjectID.from_uuid(project),
                    text=text)
        elif isinstance(id, ent.ImageID):
            tx.execute(
                    '''
                    SELECT timestamp, content_type, data
                    FROM Image
                    WHERE id = ?''', (
                        id,))
            r = tx.fetchone()
            if r is not None:
                (timestamp, content_type, data) = r
                return ent.Image(
                    id=id,
                    timestamp=timestamp,
                    content_type=content_type,
                    data=data)
        else:
            raise ValueError(id)

    def update(self, tx: sqlite3.Cursor, entity: ent.Entity) -> bool:
        """Updates an entity in the database.

        :param tx: An ongoing transaction.

        :param entity: The entity to create.

        :return: whether the entity was actually updated

        :raise ValueError: if the entity type is not supported
        """
        if isinstance(entity, ent.Project):
            tx.execute('''
                UPDATE Project
                SET name = ?, description = ?
                WHERE id = ?''', (
                    entity.name,
                    entity.description,
                    entity.id))
        elif isinstance(entity, ent.Prompt):
            tx.execute('''
                UPDATE Prompt
                SET project = ?, text = ?
                WHERE id = ?''', (
                    entity.project,
                    entity.text,
                    entity.id))
        elif isinstance(entity, ent.Image):
            tx.execute('''
                UPDATE Image
                SET timestamp = ?, content_type = ?, data = ?
                WHERE id = ?''', (
                    entity.timestamp,
                    entity.content_type,
                    entity.data,
                    entity.id))
        else:
            raise ValueError(entity)

        return tx.rowcount > 0

    def delete(self, tx: sqlite3.Cursor, id: ent.ID) -> bool:
        """Deletes an entiity from the database.

        :param tx: An ongoing transaction.

        :param id: The ID of the entity to delete.

        :return: whether the entity was actually deleted

        :raise ValueError: if the entity type is not supported
        """
        if isinstance(id, ent.ProjectID):
            tx.execute('''
                DELETE FROM Project
                WHERE id = ?''', (
                    id,))
        elif isinstance(id, ent.PromptID):
            tx.execute('''
                DELETE FROM Prompt
                WHERE id = ?''', (
                    id,))
        elif isinstance(id, ent.ImageID):
            tx.execute('''
                DELETE FROM Image
                WHERE id = ?''', (
                    id,))
        else:
            raise ValueError(id)

        return tx.rowcount > 0

    def link(self, tx: sqlite3.Cursor, parent: ent.Entity, child: ent.Entity):
        """Links two entitites.

        Supported pairs are:

        *prompt* and *image*
            The image is included in the prompt.

        :param tx: An ongoing transaction.

        :param parent: The parent entity.

        :param child: The child entity.
        """
        if isinstance(parent, ent.Prompt) and isinstance(child, ent.Image):
            tx.execute('''
                INSERT INTO Prompt_Image(prompt, image)
                VALUES(?, ?)
                ''', (
                    parent.id, child.id))
        else:
            raise ValueError((parent, child))

    def icon(self, tx: sqlite3.Cursor, id: ent.ID) -> Optional[ent.Image]:
        """Loads the icon associated with an entity.

        :param tx: An ongoing transaction.

        :param id: The ID of the entity whose icon to load.

        :raise ValueError: if the entity ID type is not supported
        """
        if isinstance(id, ent.ProjectID):
            tx.execute(
                '''
                SELECT Image.id, Image.content_type, Image.timestamp,
                    Image.data
                FROM Image
                LEFT JOIN Prompt
                    ON Prompt.project = ?
                LEFT JOIN Prompt_Image
                    ON Prompt_Image.image = Image.id
                WHERE Prompt_Image.prompt = Prompt.id
                ORDER BY Image.timestamp DESC''', (
                    id,))
            r = tx.fetchone()
        elif isinstance(id, ent.PromptID):
            tx.execute(
                '''
                SELECT Image.id, Image.content_type, Image.timestamp,
                    Image.data
                FROM Image
                LEFT JOIN Prompt_Image
                    ON Prompt_Image.image = Image.id
                WHERE Prompt_Image.prompt = ?
                ORDER BY Image.timestamp DESC''', (
                    id,))
            r = tx.fetchone()
        elif isinstance(id, ent.ImageID):
            tx.execute(
                '''
                SELECT Image.id, Image.content_type, Image.timestamp,
                    Image.data
                FROM Image
                WHERE id = ?''', (
                    id,))
            r = tx.fetchone()
        else:
            raise ValueError(id)

        if r is not None:
            (id, content_type, timestamp, data) = r
            return ent.Image(
                id=id,
                timestamp=timestamp,
                content_type=content_type,
                data=data)

    def projects(
            self) -> Sequence[ent.Project]:
        """Lists all projects.

        :return: a listing of all projects
        """
        return (
            ent.Project(
                id=ent.ProjectID.from_uuid(id),
                name=name,
                description=description)
            for (id, name, description) in self._conn.execute(
                '''
                SELECT id, name, description
                FROM Project'''))

    def prompts(
            self,
            project: ent.ProjectID) -> Sequence[ent.Prompt]:
        """Loads all prompts belonging to a project.

        :param project: The project ID.

        :return: all prompts associated with the project
        """
        return (
            ent.Prompt(
                id=ent.PromptID.from_uuid(id),
                project=ent.ProjectID.from_uuid(project),
                text=text)
            for (id, project, text) in self._conn.execute(
                '''
                SELECT id, project, text
                FROM Prompt
                WHERE project = ?''', (
                    project,)))

    def images(
            self,
            prompt: ent.PromptID) -> Sequence[ent.Image]:
        """Loads all images belonging to a prompt.

        :param prompt: The prompt ID.

        :return: all images associated with the prompt
        """
        return (
            ent.Image(
                id=ent.ImageID.from_uuid(id),
                timestamp=timestamp,
                content_type=content_type,
                data=None)
            for (id, content_type, timestamp) in self._conn.execute(
                    '''
                    SELECT Image.id, Image.content_type, Image.timestamp
                    FROM Image
                    LEFT JOIN Prompt_Image
                        ON Prompt_Image.image = Image.id
                    WHERE Prompt_Image.prompt = ?
                    ORDER BY Image.timestamp ASC''', (
                        prompt,)))

    def now(self) -> int:
        """The current timestamp.

        :return: the timestamp when this method was called
        """
        return datetime.now().timestamp()
