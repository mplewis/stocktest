"""Data fetching from yfinance with retry logic and caching."""

import asyncio
import random
import time
from datetime import datetime
from functools import wraps

import pandas as pd
import structlog
import yfinance as yf
from tqdm import tqdm

from stocktest.data.cache import (
    cache_price_data,
    find_missing_ranges,
    load_price_data,
    update_cache_metadata,
)
from stocktest.data.database import get_engine, get_session

logger = structlog.get_logger()


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
def fetch_with_retry(ticker: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
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


async def fetch_ticker_async(
    ticker: str,
    start_date: datetime,
    end_date: datetime,
    db_path: str | None,
    semaphore: asyncio.Semaphore,
    pbar: tqdm,
) -> tuple[str, pd.DataFrame | None]:
    """Fetch data for a single ticker asynchronously with semaphore control."""
    async with semaphore:
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None,
                fetch_price_data,
                ticker,
                start_date,
                end_date,
                db_path,
                0,
            )
            pbar.update(1)
            return ticker, data
        except Exception as e:
            logger.warning("failed to fetch ticker", ticker=ticker, error=str(e))
            pbar.update(1)
            return ticker, None


async def fetch_multiple_tickers_async(
    tickers: list[str],
    start_date: datetime,
    end_date: datetime,
    db_path: str | None = None,
    max_concurrent: int = 5,
) -> dict[str, pd.DataFrame]:
    """Fetch data for multiple tickers in parallel with concurrency control and progress bar."""
    semaphore = asyncio.Semaphore(max_concurrent)
    results = {}

    with tqdm(total=len(tickers), desc="Fetching tickers", unit="ticker") as pbar:
        tasks = [
            fetch_ticker_async(ticker, start_date, end_date, db_path, semaphore, pbar)
            for ticker in tickers
        ]
        completed = await asyncio.gather(*tasks)

        for ticker, data in completed:
            results[ticker] = data

    return results


def fetch_multiple_tickers(
    tickers: list[str],
    start_date: datetime,
    end_date: datetime,
    db_path: str | None = None,
    delay: float = 0.5,
    max_concurrent: int = 5,
) -> dict[str, pd.DataFrame]:
    """Fetch data for multiple tickers with parallelization and progress bar.

    Args:
        tickers: List of ticker symbols to fetch
        start_date: Start date for data
        end_date: End date for data
        db_path: Path to database for caching
        delay: Deprecated - kept for backward compatibility, ignored
        max_concurrent: Maximum number of concurrent requests (default: 5)

    Returns:
        Dictionary mapping ticker symbols to DataFrames
    """
    return asyncio.run(
        fetch_multiple_tickers_async(tickers, start_date, end_date, db_path, max_concurrent)
    )
