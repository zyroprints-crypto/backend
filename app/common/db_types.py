"""
Portable column types that render as native, efficient types on PostgreSQL
(UUID, JSONB, ARRAY) but degrade gracefully on SQLite so the same models
work against the production database and against a fast in-memory SQLite
database in unit tests.
"""
import uuid

from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import CHAR, JSON, TypeDecorator


class GUID(TypeDecorator):
    """Platform-independent UUID: native UUID on Postgres, CHAR(36) elsewhere."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        return str(value if isinstance(value, uuid.UUID) else uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


PortableJSON = JSON().with_variant(PG_JSONB, "postgresql")


def PortableArray(item_type):
    """Native ARRAY on Postgres; JSON-encoded list everywhere else."""
    return JSON().with_variant(PG_ARRAY(item_type), "postgresql")
