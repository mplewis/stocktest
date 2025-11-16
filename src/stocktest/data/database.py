"""Database engine and session management."""

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from stocktest.data.models import Base


def get_engine(db_path: Path | str | None = None):
    """Create and return a SQLAlchemy engine."""
    db_path = Path("data/stocktest.db") if db_path is None else Path(db_path)

    db_path.parent.mkdir(parents=True, exist_ok=True)

    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, echo=False)

    Base.metadata.create_all(engine)

    return engine


@contextmanager
def get_session(engine=None):
    """Context manager for database sessions."""
    if engine is None:
        engine = get_engine()

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
