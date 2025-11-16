"""Tests for company information fetching."""

from unittest.mock import Mock, patch

from stocktest.data.company_info import fetch_company_name


def test_fetches_company_name_from_yfinance():
    """Fetches company name from yfinance."""
    with patch("stocktest.data.company_info.yf.Ticker") as mock_ticker:
        mock_obj = Mock()
        mock_obj.info = {"longName": "Apple Inc."}
        mock_ticker.return_value = mock_obj

        result = fetch_company_name("AAPL")

        assert result == "Apple Inc."
        mock_ticker.assert_called_once_with("AAPL")


def test_falls_back_to_short_name():
    """Falls back to shortName if longName not available."""
    with patch("stocktest.data.company_info.yf.Ticker") as mock_ticker:
        mock_obj = Mock()
        mock_obj.info = {"shortName": "Apple"}
        mock_ticker.return_value = mock_obj

        result = fetch_company_name("AAPL")

        assert result == "Apple"


def test_returns_ticker_if_no_name_available():
    """Returns ticker symbol if no name data available."""
    with patch("stocktest.data.company_info.yf.Ticker") as mock_ticker:
        mock_obj = Mock()
        mock_obj.info = {}
        mock_ticker.return_value = mock_obj

        result = fetch_company_name("UNKNOWN")

        assert result == "UNKNOWN"


def test_returns_ticker_on_exception():
    """Returns ticker symbol when API call fails."""
    with patch("stocktest.data.company_info.yf.Ticker") as mock_ticker:
        mock_ticker.side_effect = Exception("API error")

        result = fetch_company_name("AAPL")

        assert result == "AAPL"
