"""Database engine and session management."""
from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine, event, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from database import models  # noqa: F401 - register ORM models
from database.base import Base

def build_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine and prepare local SQLite storage if needed."""
    url = make_url(database_url)
    connect_args: dict[str, object] = {}
    if url.drivername == "sqlite":
        if url.database not in {None, "", ":memory:"}:
            database_path = Path(url.database).expanduser()
            if not database_path.is_absolute():
                database_path = Path.cwd() / database_path
            database_path.parent.mkdir(parents=True, exist_ok=True)
        connect_args["check_same_thread"] = False
    engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
    if url.drivername == "sqlite":
        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA foreign_keys=ON")
            finally:
                cursor.close()
    return engine

@lru_cache(maxsize=4)
def get_engine(database_url: str) -> Engine:
    """Return a cached engine for a database URL."""
    return build_engine(database_url)

def get_session_factory(database_url: str) -> sessionmaker[Session]:
    """Create a session factory bound to the requested database."""
    return sessionmaker(bind=get_engine(database_url), autoflush=False, expire_on_commit=False)

def get_session(database_url: str) -> Iterator[Session]:
    """Yield a session and always close it."""
    session = get_session_factory(database_url)()
    try:
        yield session
    finally:
        session.close()

def initialize_database(database_url: str) -> None:
    """Create missing tables and apply the supported SQLite compatibility change."""
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)
    if engine.dialect.name != "sqlite":
        return
    inspector = inspect(engine)
    if not inspector.has_table("order_line_items"):
        return
    columns = {column["name"] for column in inspector.get_columns("order_line_items")}
    if "product_id" not in columns:
        with engine.begin() as connection:
            connection.execute(text(
                "ALTER TABLE order_line_items ADD COLUMN product_id INTEGER "
                "REFERENCES products(id) ON DELETE RESTRICT"
            ))
