"""Database engine and session factory."""

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_database_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_database_settings()
    return create_engine(settings.database_url, echo=settings.database_echo, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


@contextmanager
def session_scope() -> Iterator[Session]:
    """A unit of work: commit on success, roll back on any error."""
    with get_session_factory().begin() as session:
        yield session
