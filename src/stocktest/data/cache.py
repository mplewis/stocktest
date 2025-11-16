"""Cache operations for price data using SQLAlchemy ORM."""

import time
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from stocktest.data.models import CacheMetadata, Price, Security


def to_cents(value: float) -> int:
    """Convert dollar value to integer cents."""
    return int(round(value * 100))


def to_dollars(cents: int) -> float:
    """Convert integer cents to dollar value."""
    return cents / 100.0


def get_or_create_security(session: Session, ticker: str) -> Security:
    """Get or create a security by ticker symbol."""
    security = session.query(Security).filter_by(ticker=ticker).first()

    if security is None:
        now = int(time.time())
        security = Security(
            ticker=ticker,
            created_at=now,
            updated_at=now,
        )
        session.add(security)
        session.flush()

    return security


def cache_price_data(session: Session, ticker: str, df: pd.DataFrame) -> None:
    """Cache price data for a security using bulk insert."""
    security = get_or_create_security(session, ticker)

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
        pd.Timestamp(end_date)
        .tz_localize("UTC")
        .replace(hour=23, minute=59, second=59)
        .timestamp()
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

    index = [datetime.fromtimestamp(p.timestamp) for p in prices]

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

    missing = []

    if start_ts < cached_start:
        missing.append((start_date, datetime.fromtimestamp(cached_start)))

    if end_ts > cached_end:
        missing.append((datetime.fromtimestamp(cached_end), end_date))

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
