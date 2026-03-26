from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker


def build_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine with sane defaults."""
    return create_engine(database_url, future=True, echo=False, pool_pre_ping=True)


def make_scoped_session(engine: Engine):
    """Return a scoped session factory bound to the given engine."""
    return scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))
