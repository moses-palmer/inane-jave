"""
Database entities
-----------------

The classes in this module correspond to entities in the database.
"""
import sqlite3
import uuid

from dataclasses import dataclass, field, fields, Field
from typing import Any, Optional, Union, get_args, get_origin
from uuid import UUID


class ID:
    """A simple base class wrapping a UUID.
    """
    @classmethod
    def new(cls) -> Any:
        """Constructs a new random value.
        """
        return cls(id=uuid.uuid4())

    @classmethod
    def from_uuid(cls, uuid: bytes) -> Any:
        """Constructs a value from its binary representation.

        :param uuid: The binary encoding of the UUID.
        """
        return cls(UUID(bytes=uuid))

    @classmethod
    def from_string(cls, s: str) -> Any:
        """Constructs a value from its string representation.

        :param s: The string encoding of the UUID.
        """
        return cls(UUID(hex=s))

    @property
    def bytes(self):
        """The binary representation of this value.
        """
        return self.id.bytes

    def __str__(self):
        return str(self.id)

    def __conform__(self, protocol):
        if protocol is sqlite3.PrepareProtocol:
            return self.bytes


class Entity:
    """A simple base class providing JSON serialisation.

    This class also provides simple type-checking.
    """
    def to_json(self):
        """Converts this entity to JSON.

        :return: a dict
        """
        return {
            field.name: self._json_serialize_field(field)
            for field in fields(self)}

    @classmethod
    def from_json(cls, data: dict) -> Any:
        """Converts a JSON respresentation to an entity.

        :param data: The JSON representation.

        :return: an entity
        """
        return cls(**{
            field.name: cls._json_deserialize_field(
                field,
                data.get(field.name, None))
            for field in fields(cls)})

    def validate_fields(self) -> Any:
        """Validates all fields according to their specified type.

        :return: this object
        """
        for field in fields(self):
            origin = get_origin(field.type)
            value = getattr(self, field.name)
            if origin is Union:
                if not any(
                        isinstance(value, arg)
                        for arg in get_args(field.type)):
                    raise ValueError(field.name)
            elif origin is None and not isinstance(value, field.type):
                setattr(self, field.name, field.type(value))
        return self

    def _json_serialize_field(self, field: Field) -> Any:
        """Extracts the JSON value of a field.

        :param field: The field whose value to extract.

        :return: a JSON serialisable value
        """
        value = getattr(self, field.name)
        if isinstance(value, Entity):
            return value.to_json()
        elif isinstance(value, ID):
            return str(value.id)
        else:
            return value

    @classmethod
    def _json_deserialize_field(cls, field: Field, value: Any) -> Any:
        """Converts a field and JSON value to a field value.

        :param field: The field whose value to set.

        :param value: The value to set.

        :return: a converted value
        """
        if type(field.type) == type:
            if issubclass(field.type, Entity):
                return value.from_json(value)
            elif issubclass(field.type, ID):
                return field.type.from_string(value)
            else:
                return value
        else:
            return value

    def __post_init__(self):
        self.validate_fields()


@dataclass(frozen=True, eq=True)
class ProjectID(ID):
    """A typed ID.
    """
    id: UUID


@dataclass
class Project(Entity):
    """A project.

    This is the top level entity.
    """
    #: The database ID.
    id: ProjectID

    #: The name of this project.
    name: str

    #: A short description of this project.
    description: str


@dataclass(frozen=True, eq=True)
class PromptID(ID):
    """A typed ID.
    """
    id: UUID


@dataclass
class Prompt(Entity):
    """A given prompt.
    """
    #: The database ID.
    id: PromptID

    #: The project to which this prompt belongs
    project: ProjectID

    #: The actual prompt.
    text: str


@dataclass(frozen=True, eq=True)
class ImageID(ID):
    """A typed ID.
    """
    id: UUID


@dataclass
class Image(Entity):
    """A stored image.
    """
    #: The database ID.
    id: ImageID

    #: The timestamp, expressed as a UNIX timestamp, of creation.
    timestamp: int

    #: The content type of the image.
    content_type: str

    #: The actual data.
    data: Optional[bytes] = field(repr=False)

    @property
    def data_is_loaded(self) -> bool:
        """Whether the data has been loaded.
        """
        return self.data is not None

    def unload(self) -> Entity:
        """Returns a copy of this image with ``data`` cleared.

        :return: a new unloaded image
        """
        return Image(
            id=self.id,
            timestamp=self.timestamp,
            content_type=self.content_type,
            data=None)
