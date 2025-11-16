"""Tests for cache operations."""

from datetime import datetime

import pandas as pd

from stocktest.data.cache import (
    cache_price_data,
    find_missing_ranges,
    get_or_create_security,
    load_price_data,
    to_cents,
    to_dollars,
    update_cache_metadata,
)
from stocktest.data.database import get_engine, get_session
from stocktest.data.models import CacheMetadata, Security


def test_converts_dollars_to_cents():
    """Converts dollar values to integer cents."""
    assert to_cents(10.50) == 1050
    assert to_cents(0.01) == 1
    assert to_cents(100.00) == 10000


def test_converts_cents_to_dollars():
    """Converts integer cents to dollar values."""
    assert to_dollars(1050) == 10.50
    assert to_dollars(1) == 0.01
    assert to_dollars(10000) == 100.00


def test_gets_or_creates_security(tmp_path):
    """Gets or creates a security by ticker."""
    db_path = tmp_path / "test.db"
    engine = get_engine(db_path)

    with get_session(engine) as session:
        security1 = get_or_create_security(session, "VTI")
        assert security1.ticker == "VTI"
        assert security1.id is not None

        security2 = get_or_create_security(session, "VTI")
        assert security2.id == security1.id


def test_caches_price_data(tmp_path):
    """Caches price data using bulk insert."""
    db_path = tmp_path / "test.db"
    engine = get_engine(db_path)

    df = pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [102.0, 103.0],
            "Low": [99.0, 100.0],
            "Close": [101.0, 102.0],
            "Volume": [1000000, 1100000],
            "Adj Close": [101.0, 102.0],
        },
        index=[
            datetime(2020, 1, 1),
            datetime(2020, 1, 2),
        ],
    )

    with get_session(engine) as session:
        cache_price_data(session, "VTI", df)

    with get_session(engine) as session:
        loaded = load_price_data(
            session, "VTI", datetime(2020, 1, 1), datetime(2020, 1, 2)
        )

    assert loaded is not None
    assert len(loaded) == 2
    assert loaded.iloc[0]["Open"] == 100.0
    assert loaded.iloc[1]["Close"] == 102.0


def test_loads_price_data_from_cache(tmp_path):
    """Loads price data from cache with date filtering."""
    db_path = tmp_path / "test.db"
    engine = get_engine(db_path)

    df = pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0],
            "High": [102.0, 103.0, 104.0],
            "Low": [99.0, 100.0, 101.0],
            "Close": [101.0, 102.0, 103.0],
            "Volume": [1000000, 1100000, 1200000],
            "Adj Close": [101.0, 102.0, 103.0],
        },
        index=[
            datetime(2020, 1, 1),
            datetime(2020, 1, 2),
            datetime(2020, 1, 3),
        ],
    )

    with get_session(engine) as session:
        cache_price_data(session, "VTI", df)

    with get_session(engine) as session:
        loaded = load_price_data(
            session, "VTI", datetime(2020, 1, 2), datetime(2020, 1, 3)
        )

    assert loaded is not None
    assert len(loaded) == 2
    assert loaded.iloc[0]["Close"] == 102.0


def test_detects_gaps_in_cache(tmp_path):
    """Detects missing date ranges in cached data."""
    db_path = tmp_path / "test.db"
    engine = get_engine(db_path)

    df = pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [102.0, 103.0],
            "Low": [99.0, 100.0],
            "Close": [101.0, 102.0],
            "Volume": [1000000, 1100000],
            "Adj Close": [101.0, 102.0],
        },
        index=[
            datetime(2020, 1, 15),
            datetime(2020, 1, 16),
        ],
    )

    with get_session(engine) as session:
        cache_price_data(session, "VTI", df)

    with get_session(engine) as session:
        missing = find_missing_ranges(
            session, "VTI", datetime(2020, 1, 1), datetime(2020, 1, 31)
        )

    assert len(missing) == 2
    assert missing[0][0] == datetime(2020, 1, 1)
    assert missing[1][1] == datetime(2020, 1, 31)


def test_updates_cache_metadata(tmp_path):
    """Updates cache metadata after successful fetch."""
    db_path = tmp_path / "test.db"
    engine = get_engine(db_path)

    df = pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [102.0, 103.0],
            "Low": [99.0, 100.0],
            "Close": [101.0, 102.0],
            "Volume": [1000000, 1100000],
            "Adj Close": [101.0, 102.0],
        },
        index=[
            datetime(2020, 1, 1),
            datetime(2020, 1, 2),
        ],
    )

    with get_session(engine) as session:
        cache_price_data(session, "VTI", df)
        update_cache_metadata(session, "VTI")

    with get_session(engine) as session:
        security = session.query(Security).filter_by(ticker="VTI").first()
        metadata = (
            session.query(CacheMetadata).filter_by(security_id=security.id).first()
        )

        assert metadata is not None
        assert metadata.total_records == 2
        assert metadata.earliest_data is not None
        assert metadata.latest_data is not None
