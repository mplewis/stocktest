"""Tests for data fetcher with mocked yfinance."""

import time
from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from stocktest.data.fetcher import (
    fetch_multiple_tickers,
    fetch_price_data,
    fetch_with_retry,
    retry_with_backoff,
)


def test_retries_with_exponential_backoff():
    """Retries failed requests with exponential backoff."""
    call_count = 0
    call_times = []

    @retry_with_backoff(max_retries=3, base_delay=0.1)
    def failing_function():
        nonlocal call_count
        call_count += 1
        call_times.append(time.time())
        if call_count < 3:
            raise ValueError("Test error")
        return "success"

    result = failing_function()

    assert result == "success"
    assert call_count == 3

    if len(call_times) >= 2:
        first_delay = call_times[1] - call_times[0]
        assert first_delay >= 0.1


def test_raises_after_max_retries():
    """Raises exception after max retries exhausted."""
    call_count = 0

    @retry_with_backoff(max_retries=2, base_delay=0.05)
    def always_failing():
        nonlocal call_count
        call_count += 1
        raise ValueError("Always fails")

    with pytest.raises(ValueError, match="Always fails"):
        always_failing()

    assert call_count == 2


@patch("stocktest.data.fetcher.yf.Ticker")
def test_fetches_data_from_yfinance(mock_ticker_class, tmp_path):
    """Fetches stock data from yfinance API."""
    mock_ticker = Mock()
    mock_ticker_class.return_value = mock_ticker

    mock_df = pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [102.0, 103.0],
            "Low": [99.0, 100.0],
            "Close": [101.0, 102.0],
            "Volume": [1000000, 1100000],
        },
        index=[datetime(2020, 1, 1), datetime(2020, 1, 2)],
    )
    mock_ticker.history.return_value = mock_df

    result = fetch_with_retry("VTI", datetime(2020, 1, 1), datetime(2020, 1, 2))

    assert len(result) == 2
    assert result.iloc[0]["Close"] == 101.0
    mock_ticker_class.assert_called_once_with("VTI")


@patch("stocktest.data.fetcher.yf.Ticker")
def test_uses_cache_first_strategy(mock_ticker_class, tmp_path):
    """Uses cache-first strategy for data retrieval."""
    db_path = tmp_path / "test.db"

    mock_ticker = Mock()
    mock_ticker_class.return_value = mock_ticker

    mock_df = pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [102.0, 103.0],
            "Low": [99.0, 100.0],
            "Close": [101.0, 102.0],
            "Volume": [1000000, 1100000],
            "Adj Close": [101.0, 102.0],
        },
        index=[datetime(2020, 1, 1), datetime(2020, 1, 2)],
    )
    mock_ticker.history.return_value = mock_df

    result1 = fetch_price_data(
        "VTI", datetime(2020, 1, 1), datetime(2020, 1, 2), db_path=str(db_path), delay=0
    )

    result2 = fetch_price_data(
        "VTI", datetime(2020, 1, 1), datetime(2020, 1, 2), db_path=str(db_path), delay=0
    )

    assert len(result1) == 2
    assert len(result2) == 2
    assert mock_ticker.history.call_count == 1


@patch("stocktest.data.fetcher.yf.Ticker")
@patch("stocktest.data.fetcher.time.sleep")
def test_delays_between_requests(mock_sleep, mock_ticker_class, tmp_path):
    """Adds delays between ticker requests to avoid rate limiting."""
    db_path = tmp_path / "test.db"

    mock_ticker = Mock()
    mock_ticker_class.return_value = mock_ticker

    mock_df = pd.DataFrame(
        {
            "Open": [100.0],
            "High": [102.0],
            "Low": [99.0],
            "Close": [101.0],
            "Volume": [1000000],
            "Adj Close": [101.0],
        },
        index=[datetime(2020, 1, 1)],
    )
    mock_ticker.history.return_value = mock_df

    tickers = ["VTI", "VOO", "VEA"]
    fetch_multiple_tickers(
        tickers,
        datetime(2020, 1, 1),
        datetime(2020, 1, 2),
        db_path=str(db_path),
        delay=0.5,
    )

    assert mock_sleep.call_count >= 2
