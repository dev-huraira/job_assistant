from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base class every ORM model inherits from."""


def init_db() -> None:
    """Create all tables that don't already exist.

    In a larger production app you'd use Alembic migrations instead of
    this, so schema changes are tracked and reversible. For this project's
    scope, create_all is simpler and sufficient.
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency: yield a DB session and always close it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()