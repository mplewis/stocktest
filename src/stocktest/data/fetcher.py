"""Data fetching from yfinance with retry logic and caching."""

import random
import time
from datetime import datetime
from functools import wraps

import pandas as pd
import yfinance as yf

from stocktest.data.cache import (
    cache_price_data,
    find_missing_ranges,
    load_price_data,
    update_cache_metadata,
)
from stocktest.data.database import get_engine, get_session


def retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=60.0):
    """Decorator for exponential backoff with jitter retry logic."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt == max_retries - 1:
                        raise

                    delay = min(base_delay * (2**attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.1)
                    sleep_time = delay + jitter

                    time.sleep(sleep_time)

            return func(*args, **kwargs)

        return wrapper

    return decorator


@retry_with_backoff(max_retries=3)
def fetch_with_retry(
    ticker: str, start_date: datetime, end_date: datetime
) -> pd.DataFrame:
    """Fetch stock data from yfinance with retry logic."""
    ticker_obj = yf.Ticker(ticker)
    df = ticker_obj.history(start=start_date, end=end_date)

    if df.empty:
        raise ValueError(f"No data returned for {ticker}")

    return df


def fetch_price_data(
    ticker: str,
    start_date: datetime,
    end_date: datetime,
    db_path: str | None = None,
    delay: float = 0.5,
) -> pd.DataFrame:
    """Fetch price data with cache-first strategy."""
    engine = get_engine(db_path)

    with get_session(engine) as session:
        cached_data = load_price_data(session, ticker, start_date, end_date)

        if cached_data is not None and len(cached_data) > 0:
            missing_ranges = find_missing_ranges(session, ticker, start_date, end_date)

            if not missing_ranges:
                return cached_data

            for missing_start, missing_end in missing_ranges:
                if delay > 0:
                    time.sleep(delay)

                new_data = fetch_with_retry(ticker, missing_start, missing_end)

                cache_price_data(session, ticker, new_data)
                update_cache_metadata(session, ticker)

            return load_price_data(session, ticker, start_date, end_date)

        else:
            if delay > 0:
                time.sleep(delay)

            data = fetch_with_retry(ticker, start_date, end_date)

            cache_price_data(session, ticker, data)
            update_cache_metadata(session, ticker)

            return data


def fetch_multiple_tickers(
    tickers: list[str],
    start_date: datetime,
    end_date: datetime,
    db_path: str | None = None,
    delay: float = 0.5,
) -> dict[str, pd.DataFrame]:
    """Fetch data for multiple tickers with rate limiting."""
    results = {}

    for i, ticker in enumerate(tickers):
        if i > 0 and delay > 0:
            time.sleep(delay)

        try:
            results[ticker] = fetch_price_data(
                ticker, start_date, end_date, db_path, delay=0
            )
        except Exception as e:
            print(f"Warning: Failed to fetch {ticker}: {e}")
            results[ticker] = None

    return results
