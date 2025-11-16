"""Tests for reporting functionality."""

from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from stocktest.analysis.reporting import (
    create_report_directory,
    export_equity_curve,
    export_summary_stats,
    export_trade_log,
)
from stocktest.backtest.engine import Portfolio


def test_exports_equity_curve_to_csv(tmp_path):
    """Exports equity curve to CSV file."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 11000, 12000], "cash": [1000, 500, 0]},
        index=[datetime(2020, 1, 1), datetime(2020, 6, 1), datetime(2021, 1, 1)],
    )

    output_path = tmp_path / "equity_curve.csv"
    export_equity_curve(equity_curve, output_path)

    assert output_path.exists()

    loaded = pd.read_csv(output_path, index_col=0, parse_dates=True)
    assert len(loaded) == 3
    assert "total_value" in loaded.columns
    assert "cash" in loaded.columns


def test_creates_parent_directories_for_equity_curve(tmp_path):
    """Creates parent directories if they don't exist."""
    output_path = tmp_path / "subdir" / "equity_curve.csv"

    equity_curve = pd.DataFrame(
        {"total_value": [10000, 11000]},
        index=[datetime(2020, 1, 1), datetime(2021, 1, 1)],
    )

    export_equity_curve(equity_curve, output_path)

    assert output_path.exists()
    assert output_path.parent.exists()


def test_raises_on_empty_equity_curve(tmp_path):
    """Raises ValueError for empty DataFrame."""
    equity_curve = pd.DataFrame()
    output_path = tmp_path / "equity.csv"

    with pytest.raises(ValueError, match="equity_curve cannot be empty"):
        export_equity_curve(equity_curve, output_path)


def test_exports_trade_log_to_csv(tmp_path):
    """Exports trade log to CSV file."""
    portfolio = Portfolio(initial_capital=10000.0)
    portfolio.history = [
        {
            "date": datetime(2020, 1, 1),
            "total_value": 10000,
            "cash": 5000,
            "positions": {},
            "trades": [
                {
                    "ticker": "VTI",
                    "shares": 50,
                    "price": 100,
                    "value": 5000,
                    "cost": 5,
                }
            ],
        },
        {
            "date": datetime(2020, 1, 2),
            "total_value": 11000,
            "cash": 4000,
            "positions": {},
            "trades": [
                {
                    "ticker": "BND",
                    "shares": 25,
                    "price": 80,
                    "value": 2000,
                    "cost": 2,
                }
            ],
        },
    ]

    output_path = tmp_path / "trades.csv"
    export_trade_log(portfolio, output_path)

    assert output_path.exists()

    loaded = pd.read_csv(output_path)
    assert len(loaded) == 2
    assert "ticker" in loaded.columns
    assert "shares" in loaded.columns
    assert "price" in loaded.columns
    assert loaded.iloc[0]["ticker"] == "VTI"
    assert loaded.iloc[1]["ticker"] == "BND"


def test_raises_on_empty_portfolio_history(tmp_path):
    """Raises ValueError when portfolio has no history."""
    portfolio = Portfolio(initial_capital=10000.0)
    output_path = tmp_path / "trades.csv"

    with pytest.raises(ValueError, match="portfolio has no trade history"):
        export_trade_log(portfolio, output_path)


def test_raises_on_no_trades_in_history(tmp_path):
    """Raises ValueError when portfolio history has no trades."""
    portfolio = Portfolio(initial_capital=10000.0)
    portfolio.history = [
        {
            "date": datetime(2020, 1, 1),
            "total_value": 10000,
            "cash": 10000,
            "positions": {},
            "trades": [],
        }
    ]

    output_path = tmp_path / "trades.csv"

    with pytest.raises(ValueError, match="no trades found in portfolio history"):
        export_trade_log(portfolio, output_path)


def test_exports_summary_stats_to_csv(tmp_path):
    """Exports summary statistics to CSV file."""
    metrics = {
        "total_return": 0.25,
        "cagr": 0.12,
        "sharpe_ratio": 1.5,
        "max_drawdown": 0.15,
    }

    output_path = tmp_path / "summary.csv"
    export_summary_stats(metrics, output_path)

    assert output_path.exists()

    loaded = pd.read_csv(output_path)
    assert len(loaded) == 4
    assert "metric" in loaded.columns
    assert "value" in loaded.columns
    assert loaded[loaded["metric"] == "total_return"]["value"].iloc[0] == 0.25


def test_raises_on_empty_metrics(tmp_path):
    """Raises ValueError for empty metrics dictionary."""
    metrics = {}
    output_path = tmp_path / "summary.csv"

    with pytest.raises(ValueError, match="metrics dictionary cannot be empty"):
        export_summary_stats(metrics, output_path)


def test_creates_report_directory_structure(tmp_path):
    """Creates report directory with subdirectories."""
    report_path = create_report_directory(tmp_path, "backtest_2020")

    assert report_path.exists()
    assert (report_path / "charts").exists()
    assert (report_path / "data").exists()


def test_handles_existing_report_directory(tmp_path):
    """Handles existing report directory gracefully."""
    report_name = "backtest_2020"

    path1 = create_report_directory(tmp_path, report_name)
    path2 = create_report_directory(tmp_path, report_name)

    assert path1 == path2
    assert path1.exists()


def test_creates_nested_report_directories(tmp_path):
    """Creates nested report directories."""
    base_path = tmp_path / "output" / "reports"
    report_path = create_report_directory(base_path, "backtest_2020")

    assert report_path.exists()
    assert report_path == base_path / "backtest_2020"


def test_export_handles_string_paths(tmp_path):
    """Handles string paths correctly."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 11000]},
        index=[datetime(2020, 1, 1), datetime(2021, 1, 1)],
    )

    output_path = str(tmp_path / "equity.csv")
    export_equity_curve(equity_curve, output_path)

    assert Path(output_path).exists()
