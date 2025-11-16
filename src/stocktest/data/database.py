"""Database engine and session management."""

import logging
import sys
from contextlib import contextmanager
from io import StringIO
from pathlib import Path

import structlog
from alembic import command
from alembic.config import Config as AlembicConfig
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = structlog.get_logger()


def run_migrations(db_path: Path):
    """Run Alembic migrations to ensure database is up to date.

    Args:
        db_path: Path to the database file
    """
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        alembic_ini = project_root / "alembic.ini"

        if not alembic_ini.exists():
            return

        alembic_cfg = AlembicConfig(str(alembic_ini))
        alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
        alembic_cfg.attributes["configure_logger"] = False

        alembic_logger = logging.getLogger("alembic")
        original_level = alembic_logger.level
        alembic_logger.setLevel(logging.CRITICAL)

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            command.upgrade(alembic_cfg, "head")
        finally:
            sys.stdout = old_stdout
            alembic_logger.setLevel(original_level)
    except Exception:
        pass


def get_engine(db_path: Path | str | None = None):
    """Create and return a SQLAlchemy engine.

    Args:
        db_path: Path to database file (default: data/stocktest.db)

    Returns:
        SQLAlchemy engine with migrations run
    """
    db_path = Path("data/stocktest.db") if db_path is None else Path(db_path)

    db_path.parent.mkdir(parents=True, exist_ok=True)

    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, echo=False)

    run_migrations(db_path)

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
