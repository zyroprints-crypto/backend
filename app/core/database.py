"""
SQLAlchemy 2.x engine / session setup.
Provides a FastAPI dependency `get_db` that yields a scoped session
and guarantees rollback + close on error.
"""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


_engine_kwargs = {"pool_pre_ping": True, "echo": settings.DB_ECHO}
if not settings.DATABASE_URL.startswith("sqlite"):
    # SQLite (used for local/unit testing) doesn't support pool_size/max_overflow.
    _engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    _engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
