"""Tests for backtesting engine."""

from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

from stocktest.backtest.engine import (
    BacktestConfig,
    Portfolio,
    _get_rebalance_dates,
    run_backtest,
)


def test_initializes_portfolio():
    """Initializes portfolio with starting capital."""
    portfolio = Portfolio(initial_capital=10000.0, transaction_cost_pct=0.1)

    assert portfolio.initial_capital == 10000.0
    assert portfolio.cash == 10000.0
    assert portfolio.transaction_cost_pct == 0.1
    assert portfolio.positions == {}
    assert portfolio.history == []


def test_calculates_position_value():
    """Calculates current value of a position."""
    portfolio = Portfolio(initial_capital=10000.0)
    portfolio.positions["VTI"] = 50.0

    value = portfolio.get_position_value("VTI", 100.0)

    assert value == 5000.0


def test_calculates_total_portfolio_value():
    """Calculates total portfolio value including cash and positions."""
    portfolio = Portfolio(initial_capital=10000.0)
    portfolio.cash = 5000.0
    portfolio.positions["VTI"] = 25.0
    portfolio.positions["BND"] = 50.0

    prices = {"VTI": 100.0, "BND": 80.0}
    total = portfolio.get_total_value(prices)

    assert total == 5000.0 + 2500.0 + 4000.0


def test_calculates_transaction_cost():
    """Calculates transaction cost based on percentage."""
    portfolio = Portfolio(initial_capital=10000.0, transaction_cost_pct=0.1)

    cost = portfolio.calculate_transaction_cost(5000.0)

    assert cost == 5.0


def test_rebalances_portfolio():
    """Rebalances portfolio to target weights."""
    portfolio = Portfolio(initial_capital=10000.0, transaction_cost_pct=0.1)

    target_weights = {"VTI": 0.6, "BND": 0.4}
    prices = {"VTI": 100.0, "BND": 80.0}
    date = datetime(2020, 1, 1)

    portfolio.rebalance(target_weights, prices, date)

    assert len(portfolio.history) == 1
    assert portfolio.history[0]["date"] == date
    assert abs(portfolio.positions["VTI"] - 60.0) < 0.1
    assert abs(portfolio.positions["BND"] - 50.0) < 0.1
    assert portfolio.cash < 10000.0


def test_rebalancing_with_transaction_costs():
    """Applies transaction costs during rebalancing."""
    portfolio = Portfolio(initial_capital=10000.0, transaction_cost_pct=0.5)

    target_weights = {"VTI": 1.0}
    prices = {"VTI": 100.0}
    date = datetime(2020, 1, 1)

    portfolio.rebalance(target_weights, prices, date)

    total_value = portfolio.get_total_value(prices)
    assert total_value < 10000.0


def test_gets_equity_curve():
    """Gets portfolio value over time as DataFrame."""
    portfolio = Portfolio(initial_capital=10000.0)

    target_weights = {"VTI": 1.0}
    prices = {"VTI": 100.0}
    portfolio.rebalance(target_weights, prices, datetime(2020, 1, 1))

    prices = {"VTI": 110.0}
    portfolio.rebalance(target_weights, prices, datetime(2020, 1, 2))

    curve = portfolio.get_equity_curve()

    assert len(curve) == 2
    assert "total_value" in curve.columns
    assert "cash" in curve.columns
    assert curve.index.name == "date"


def test_returns_empty_dataframe_with_no_history():
    """Returns empty DataFrame when no history exists."""
    portfolio = Portfolio(initial_capital=10000.0)

    curve = portfolio.get_equity_curve()

    assert curve.empty


def test_calculates_daily_rebalance_dates():
    """Calculates daily rebalancing dates."""
    dates = pd.DatetimeIndex([datetime(2020, 1, 1), datetime(2020, 1, 2), datetime(2020, 1, 3)])

    rebalance_dates = _get_rebalance_dates(dates, "daily")

    assert len(rebalance_dates) == 3


def test_calculates_weekly_rebalance_dates():
    """Calculates weekly rebalancing dates."""
    dates = pd.DatetimeIndex(
        [
            datetime(2020, 1, 6),
            datetime(2020, 1, 7),
            datetime(2020, 1, 13),
            datetime(2020, 1, 14),
        ]
    )

    rebalance_dates = _get_rebalance_dates(dates, "weekly")

    assert len(rebalance_dates) == 2


def test_calculates_monthly_rebalance_dates():
    """Calculates monthly rebalancing dates."""
    dates = pd.DatetimeIndex(
        [
            datetime(2020, 1, 15),
            datetime(2020, 1, 16),
            datetime(2020, 2, 1),
            datetime(2020, 3, 1),
        ]
    )

    rebalance_dates = _get_rebalance_dates(dates, "monthly")

    assert len(rebalance_dates) == 3


def test_raises_on_invalid_rebalance_frequency():
    """Raises ValueError for invalid rebalance frequency."""
    dates = pd.DatetimeIndex([datetime(2020, 1, 1)])

    with pytest.raises(ValueError, match="Unknown rebalance frequency"):
        _get_rebalance_dates(dates, "quarterly")


@patch("stocktest.backtest.engine.fetch_multiple_tickers")
def test_runs_backtest(mock_fetch_multiple_tickers):
    """Runs backtest with rebalancing."""
    mock_df = pd.DataFrame(
        {"Close": [100.0, 110.0, 120.0]},
        index=[datetime(2020, 1, 1), datetime(2020, 1, 2), datetime(2020, 1, 3)],
    )
    mock_fetch_multiple_tickers.return_value = {"VTI": mock_df}

    config = BacktestConfig(
        tickers=["VTI"],
        weights={"VTI": 1.0},
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2020, 1, 3),
        initial_capital=10000.0,
        rebalance_frequency="daily",
    )
    result = run_backtest(config)

    assert "portfolio" in result
    assert "equity_curve" in result
    assert isinstance(result["portfolio"], Portfolio)
    assert len(result["equity_curve"]) > 0


@patch("stocktest.backtest.engine.fetch_price_data")
@patch("stocktest.backtest.engine.fetch_multiple_tickers")
def test_runs_backtest_with_benchmark(mock_fetch_multiple_tickers, mock_fetch_price_data):
    """Runs backtest with benchmark comparison."""
    mock_df = pd.DataFrame(
        {"Close": [100.0, 110.0, 120.0]},
        index=[datetime(2020, 1, 1), datetime(2020, 1, 2), datetime(2020, 1, 3)],
    )
    mock_fetch_multiple_tickers.return_value = {"VTI": mock_df}
    mock_fetch_price_data.return_value = mock_df

    config = BacktestConfig(
        tickers=["VTI"],
        weights={"VTI": 1.0},
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2020, 1, 3),
        initial_capital=10000.0,
        benchmark_ticker="SPY",
    )
    result = run_backtest(config)

    assert "benchmark" in result
    assert "benchmark_value" in result["benchmark"].columns


@patch("stocktest.backtest.engine.fetch_price_data")
def test_raises_when_weights_do_not_sum_to_one(mock_fetch_price_data):
    """Raises ValueError when weights do not sum to 1.0."""
    with pytest.raises(ValueError, match="Weights must sum to 1.0"):
        config = BacktestConfig(
            tickers=["VTI", "BND"],
            weights={"VTI": 0.6, "BND": 0.3},
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2020, 1, 3),
        )
        run_backtest(config)


@patch("stocktest.backtest.engine.fetch_multiple_tickers")
def test_raises_when_no_price_data_available(mock_fetch_multiple_tickers):
    """Raises ValueError when no price data is available."""
    mock_fetch_multiple_tickers.return_value = {"VTI": None}

    with pytest.raises(ValueError, match="No price data available"):
        config = BacktestConfig(
            tickers=["VTI"],
            weights={"VTI": 1.0},
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2020, 1, 3),
        )
        run_backtest(config)


@patch("stocktest.backtest.engine.fetch_multiple_tickers")
def test_handles_multiple_tickers(mock_fetch_multiple_tickers):
    """Handles backtesting with multiple tickers."""
    vti_df = pd.DataFrame(
        {"Close": [100.0, 110.0]},
        index=[datetime(2020, 1, 1), datetime(2020, 1, 2)],
    )
    bnd_df = pd.DataFrame(
        {"Close": [80.0, 85.0]},
        index=[datetime(2020, 1, 1), datetime(2020, 1, 2)],
    )
    mock_fetch_multiple_tickers.return_value = {"VTI": vti_df, "BND": bnd_df}

    config = BacktestConfig(
        tickers=["VTI", "BND"],
        weights={"VTI": 0.6, "BND": 0.4},
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2020, 1, 2),
        initial_capital=10000.0,
    )
    result = run_backtest(config)

    assert len(result["portfolio"].positions) == 2
    assert "VTI" in result["portfolio"].positions
    assert "BND" in result["portfolio"].positions
