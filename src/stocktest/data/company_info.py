"""Company information fetching from yfinance."""

import random
import time
from functools import wraps

import structlog
import yfinance as yf

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
def fetch_company_name(ticker: str) -> str:
    """Fetch company name from yfinance.

    Args:
        ticker: Ticker symbol

    Returns:
        Company name, or ticker symbol if name not available
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        company_name = info.get("longName") or info.get("shortName") or ticker
        return company_name
    except Exception as e:
        logger.warning("failed to fetch company name", ticker=ticker, error=str(e))
        return ticker
