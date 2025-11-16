"""Cache operations for price data using SQLAlchemy ORM."""

import time
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy.orm import Session

from stocktest.data.models import CacheMetadata, NoDataRange, Price, Security

MISSING_DATA_TOLERANCE_DAYS = 3


def to_cents(value: float) -> int:
    """Convert dollar value to integer cents."""
    return int(round(value * 100))


def to_dollars(cents: int) -> float:
    """Convert integer cents to dollar value."""
    return cents / 100.0


def get_or_create_security(
    session: Session, ticker: str, company_name: str | None = None
) -> Security:
    """Get or create a security by ticker symbol.

    Args:
        session: SQLAlchemy session
        ticker: Ticker symbol
        company_name: Optional company name to store

    Returns:
        Security object
    """
    security = session.query(Security).filter_by(ticker=ticker).first()

    if security is None:
        now = int(time.time())
        security = Security(
            ticker=ticker,
            company_name=company_name,
            created_at=now,
            updated_at=now,
        )
        session.add(security)
        session.flush()
    elif company_name and not security.company_name:
        security.company_name = company_name
        security.updated_at = int(time.time())

    return security


def cache_price_data(
    session: Session, ticker: str, df: pd.DataFrame, company_name: str | None = None
) -> None:
    """Cache price data for a security using bulk insert.

    Args:
        session: SQLAlchemy session
        ticker: Ticker symbol
        df: Price data DataFrame
        company_name: Optional company name to store
    """
    security = get_or_create_security(session, ticker, company_name)

    for idx, row in df.iterrows():
        if hasattr(idx, "tz_localize"):
            ts_idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
        else:
            ts_idx = idx
        timestamp = int(ts_idx.timestamp())
        price = Price(
            security_id=security.id,
            timestamp=timestamp,
            open=to_cents(row["Open"]),
            high=to_cents(row["High"]),
            low=to_cents(row["Low"]),
            close=to_cents(row["Close"]),
            volume=int(row["Volume"]),
            adjusted_close=to_cents(row.get("Adj Close", row["Close"])),
        )
        session.add(price)


def load_price_data(
    session: Session, ticker: str, start_date: datetime, end_date: datetime
) -> pd.DataFrame | None:
    """Load price data from cache."""
    security = session.query(Security).filter_by(ticker=ticker).first()

    if security is None:
        return None

    start_ts = int(pd.Timestamp(start_date).tz_localize("UTC").timestamp())
    end_ts = int(
        pd.Timestamp(end_date).tz_localize("UTC").replace(hour=23, minute=59, second=59).timestamp()
    )

    prices = (
        session.query(Price)
        .filter(
            Price.security_id == security.id,
            Price.timestamp >= start_ts,
            Price.timestamp <= end_ts,
        )
        .order_by(Price.timestamp)
        .all()
    )

    if not prices:
        return None

    data = {
        "Open": [to_dollars(p.open) for p in prices],
        "High": [to_dollars(p.high) for p in prices],
        "Low": [to_dollars(p.low) for p in prices],
        "Close": [to_dollars(p.close) for p in prices],
        "Volume": [p.volume for p in prices],
        "Adj Close": [to_dollars(p.adjusted_close) for p in prices],
    }

    index = [
        datetime.fromtimestamp(p.timestamp, tz=timezone.utc).replace(tzinfo=None) for p in prices
    ]

    return pd.DataFrame(data, index=index)


def find_missing_ranges(
    session: Session, ticker: str, start_date: datetime, end_date: datetime
) -> list[tuple[datetime, datetime]]:
    """Find missing date ranges in cached data."""
    security = session.query(Security).filter_by(ticker=ticker).first()

    if security is None:
        return [(start_date, end_date)]

    start_ts = int(pd.Timestamp(start_date).tz_localize("UTC").timestamp())
    end_ts = int(pd.Timestamp(end_date).tz_localize("UTC").timestamp())

    prices = (
        session.query(Price.timestamp)
        .filter(
            Price.security_id == security.id,
            Price.timestamp >= start_ts,
            Price.timestamp <= end_ts,
        )
        .order_by(Price.timestamp)
        .all()
    )

    if not prices:
        return [(start_date, end_date)]

    timestamps = [p.timestamp for p in prices]
    cached_start = timestamps[0]
    cached_end = timestamps[-1]

    cached_start_dt = datetime.fromtimestamp(cached_start, tz=timezone.utc).replace(tzinfo=None)
    cached_end_dt = datetime.fromtimestamp(cached_end, tz=timezone.utc).replace(tzinfo=None)

    missing = []

    days_before = (cached_start_dt.date() - start_date.date()).days
    if days_before > MISSING_DATA_TOLERANCE_DAYS:
        missing.append((start_date, cached_start_dt))

    days_after = (end_date.date() - cached_end_dt.date()).days
    if days_after > MISSING_DATA_TOLERANCE_DAYS:
        missing.append((cached_end_dt, end_date))

    return missing


def update_cache_metadata(session: Session, ticker: str) -> None:
    """Update cache metadata after successful fetch."""
    security = session.query(Security).filter_by(ticker=ticker).first()

    if security is None:
        return

    prices = (
        session.query(Price)
        .filter(Price.security_id == security.id)
        .order_by(Price.timestamp)
        .all()
    )

    if not prices:
        return

    metadata = session.query(CacheMetadata).filter_by(security_id=security.id).first()

    now = int(time.time())
    earliest = prices[0].timestamp
    latest = prices[-1].timestamp
    total = len(prices)

    if metadata is None:
        metadata = CacheMetadata(
            security_id=security.id,
            last_fetch=now,
            earliest_data=earliest,
            latest_data=latest,
            total_records=total,
        )
        session.add(metadata)
    else:
        metadata.last_fetch = now
        metadata.earliest_data = earliest
        metadata.latest_data = latest
        metadata.total_records = total

    security.updated_at = now


def check_no_data_cached(
    session: Session, ticker: str, start_date: datetime, end_date: datetime
) -> bool:
    """Check if we have previously confirmed that no data exists for this date range.

    Args:
        session: SQLAlchemy session
        ticker: Ticker symbol
        start_date: Start of date range
        end_date: End of date range

    Returns:
        True if we have cached that no data exists for this range, False otherwise
    """
    security = session.query(Security).filter_by(ticker=ticker).first()

    if security is None:
        return False

    start_ts = int(pd.Timestamp(start_date).tz_localize("UTC").timestamp())
    end_ts = int(
        pd.Timestamp(end_date).tz_localize("UTC").replace(hour=23, minute=59, second=59).timestamp()
    )

    no_data_range = (
        session.query(NoDataRange)
        .filter(
            NoDataRange.security_id == security.id,
            NoDataRange.start_timestamp <= start_ts,
            NoDataRange.end_timestamp >= end_ts,
        )
        .first()
    )

    return no_data_range is not None


def get_company_name(session: Session, ticker: str) -> str | None:
    """Get cached company name for a ticker.

    Args:
        session: SQLAlchemy session
        ticker: Ticker symbol

    Returns:
        Company name if cached, None otherwise
    """
    security = session.query(Security).filter_by(ticker=ticker).first()
    return security.company_name if security else None


def cache_no_data_range(
    session: Session, ticker: str, start_date: datetime, end_date: datetime
) -> None:
    """Record that no data is available for this ticker and date range.

    Args:
        session: SQLAlchemy session
        ticker: Ticker symbol
        start_date: Start of date range
        end_date: End of date range
    """
    security = get_or_create_security(session, ticker)

    start_ts = int(pd.Timestamp(start_date).tz_localize("UTC").timestamp())
    end_ts = int(
        pd.Timestamp(end_date).tz_localize("UTC").replace(hour=23, minute=59, second=59).timestamp()
    )

    existing = (
        session.query(NoDataRange)
        .filter(
            NoDataRange.security_id == security.id,
            NoDataRange.start_timestamp == start_ts,
            NoDataRange.end_timestamp == end_ts,
        )
        .first()
    )

    now = int(time.time())

    if existing is None:
        no_data_range = NoDataRange(
            security_id=security.id,
            start_timestamp=start_ts,
            end_timestamp=end_ts,
            last_checked=now,
        )
        session.add(no_data_range)
    else:
        existing.last_checked = now
