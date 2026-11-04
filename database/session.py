"""Database engine and session management."""
from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from database import models  # noqa: F401 - register ORM models
from database.base import Base


def build_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine and prepare local SQLite storage if needed."""
    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite:///"):
        db_path = database_url.removeprefix("sqlite:///")
        if db_path != ":memory:":
            Path(db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        connect_args["check_same_thread"] = False

    engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)
    if database_url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


@lru_cache(maxsize=4)
def get_engine(database_url: str) -> Engine:
    """Return a cached engine for a database URL."""
    return build_engine(database_url)


def get_session_factory(database_url: str) -> sessionmaker[Session]:
    """Create a session factory bound to the requested database."""
    return sessionmaker(
        bind=get_engine(database_url), autoflush=False, expire_on_commit=False
    )


def get_session(database_url: str) -> Iterator[Session]:
    """Yield a session and always close it."""
    session = get_session_factory(database_url)()
    try:
        yield session
    finally:
        session.close()


def initialize_database(database_url: str) -> None:
    """Create missing database tables."""
    Base.metadata.create_all(get_engine(database_url))
