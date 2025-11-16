"""Tests for database engine and session management."""

from sqlalchemy import inspect

from stocktest.data.database import get_engine, get_session
from stocktest.data.models import Security


def test_creates_engine(tmp_path):
    """Creates a SQLAlchemy engine with proper tables."""
    db_path = tmp_path / "test.db"
    engine = get_engine(db_path)

    assert engine is not None

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "securities" in tables
    assert "prices" in tables
    assert "cache_metadata" in tables


def test_provides_session_context_manager(tmp_path):
    """Provides a working session context manager."""
    db_path = tmp_path / "test.db"
    engine = get_engine(db_path)

    with get_session(engine) as session:
        security = Security(
            ticker="VTI",
            name="Vanguard Total Stock Market ETF",
            asset_type="ETF",
            created_at=1000000000,
            updated_at=1000000000,
        )
        session.add(security)

    with get_session(engine) as session:
        result = session.query(Security).filter_by(ticker="VTI").first()
        assert result is not None
        assert result.name == "Vanguard Total Stock Market ETF"


def test_rolls_back_on_error(tmp_path):
    """Rolls back session on error."""
    db_path = tmp_path / "test.db"
    engine = get_engine(db_path)

    try:
        with get_session(engine) as session:
            security = Security(
                ticker="VOO",
                name="Vanguard S&P 500 ETF",
                asset_type="ETF",
                created_at=1000000000,
                updated_at=1000000000,
            )
            session.add(security)
            raise ValueError("Test error")
    except ValueError:
        pass

    with get_session(engine) as session:
        result = session.query(Security).filter_by(ticker="VOO").first()
        assert result is None
