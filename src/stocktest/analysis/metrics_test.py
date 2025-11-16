"""Tests for performance metrics."""

from datetime import datetime, timedelta

import pandas as pd

from stocktest.analysis.metrics import (
    calculate_alpha,
    calculate_beta,
    calculate_cagr,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_total_return,
    summarize_performance,
)


def test_calculates_total_return():
    """Calculates total return from initial to final value."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 11000, 12000]},
        index=[datetime(2020, 1, 1), datetime(2020, 6, 1), datetime(2021, 1, 1)],
    )

    total_return = calculate_total_return(equity_curve)

    assert abs(total_return - 0.2) < 0.001


def test_handles_empty_dataframe_for_total_return():
    """Returns 0 for empty DataFrame."""
    equity_curve = pd.DataFrame()

    total_return = calculate_total_return(equity_curve)

    assert total_return == 0.0


def test_handles_zero_initial_value():
    """Returns 0 when initial value is zero."""
    equity_curve = pd.DataFrame(
        {"total_value": [0, 1000]},
        index=[datetime(2020, 1, 1), datetime(2021, 1, 1)],
    )

    total_return = calculate_total_return(equity_curve)

    assert total_return == 0.0


def test_calculates_cagr():
    """Calculates Compound Annual Growth Rate."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 11000, 12100]},
        index=[datetime(2020, 1, 1), datetime(2021, 1, 1), datetime(2022, 1, 1)],
    )

    cagr = calculate_cagr(equity_curve)

    assert abs(cagr - 0.1) < 0.01


def test_handles_less_than_one_year():
    """Handles CAGR calculation for periods less than one year."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 10500]},
        index=[datetime(2020, 1, 1), datetime(2020, 6, 1)],
    )

    cagr = calculate_cagr(equity_curve)

    assert cagr > 0


def test_handles_empty_dataframe_for_cagr():
    """Returns 0 for empty DataFrame."""
    equity_curve = pd.DataFrame()

    cagr = calculate_cagr(equity_curve)

    assert cagr == 0.0


def test_calculates_sharpe_ratio():
    """Calculates Sharpe ratio from returns."""
    dates = [datetime(2020, 1, 1) + timedelta(days=i) for i in range(100)]
    values = [10000 * (1.001**i) for i in range(100)]

    equity_curve = pd.DataFrame({"total_value": values}, index=dates)

    sharpe = calculate_sharpe_ratio(equity_curve, risk_free_rate=0.0)

    assert sharpe > 0


def test_handles_zero_volatility():
    """Returns 0 when standard deviation is zero."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 10000, 10000]},
        index=[datetime(2020, 1, 1), datetime(2020, 1, 2), datetime(2020, 1, 3)],
    )

    sharpe = calculate_sharpe_ratio(equity_curve)

    assert sharpe == 0.0


def test_calculates_max_drawdown():
    """Calculates maximum drawdown from peak."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 12000, 9000, 11000]},
        index=[
            datetime(2020, 1, 1),
            datetime(2020, 2, 1),
            datetime(2020, 3, 1),
            datetime(2020, 4, 1),
        ],
    )

    max_dd = calculate_max_drawdown(equity_curve)

    assert abs(max_dd - 0.25) < 0.01


def test_handles_no_drawdown():
    """Returns 0 when there is no drawdown."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 11000, 12000]},
        index=[datetime(2020, 1, 1), datetime(2020, 2, 1), datetime(2020, 3, 1)],
    )

    max_dd = calculate_max_drawdown(equity_curve)

    assert max_dd >= 0
    assert max_dd < 0.01


def test_calculates_beta():
    """Calculates portfolio beta relative to benchmark."""
    dates = [datetime(2020, 1, 1) + timedelta(days=i) for i in range(100)]

    portfolio = pd.DataFrame({"total_value": [10000 * (1.002**i) for i in range(100)]}, index=dates)

    benchmark = pd.DataFrame(
        {"benchmark_value": [10000 * (1.001**i) for i in range(100)]}, index=dates
    )

    beta = calculate_beta(portfolio, benchmark)

    assert beta != 0.0


def test_handles_empty_dataframes_for_beta():
    """Returns 0 for empty DataFrames."""
    portfolio = pd.DataFrame()
    benchmark = pd.DataFrame()

    beta = calculate_beta(portfolio, benchmark)

    assert beta == 0.0


def test_handles_zero_benchmark_variance():
    """Returns 0 when benchmark has zero variance."""
    dates = [datetime(2020, 1, 1) + timedelta(days=i) for i in range(10)]

    portfolio = pd.DataFrame({"total_value": [10000 + i * 100 for i in range(10)]}, index=dates)

    benchmark = pd.DataFrame({"benchmark_value": [10000] * 10}, index=dates)

    beta = calculate_beta(portfolio, benchmark)

    assert beta == 0.0


def test_calculates_alpha():
    """Calculates portfolio alpha vs benchmark."""
    dates = [datetime(2020, 1, 1) + timedelta(days=i) for i in range(100)]

    portfolio = pd.DataFrame({"total_value": [10000 * (1.002**i) for i in range(100)]}, index=dates)

    benchmark = pd.DataFrame(
        {"benchmark_value": [10000 * (1.001**i) for i in range(100)]}, index=dates
    )

    alpha = calculate_alpha(portfolio, benchmark, risk_free_rate=0.0)

    assert alpha != 0.0


def test_handles_empty_dataframes_for_alpha():
    """Returns 0 for empty DataFrames."""
    portfolio = pd.DataFrame()
    benchmark = pd.DataFrame()

    alpha = calculate_alpha(portfolio, benchmark)

    assert alpha == 0.0


def test_summarizes_performance_without_benchmark():
    """Summarizes performance metrics without benchmark."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 11000, 12000]},
        index=[datetime(2020, 1, 1), datetime(2020, 6, 1), datetime(2021, 1, 1)],
    )

    summary = summarize_performance(equity_curve)

    assert "total_return" in summary
    assert "cagr" in summary
    assert "sharpe_ratio" in summary
    assert "max_drawdown" in summary
    assert "beta" not in summary
    assert "alpha" not in summary


def test_summarizes_performance_with_benchmark():
    """Summarizes performance metrics with benchmark."""
    dates = [datetime(2020, 1, 1) + timedelta(days=i * 30) for i in range(12)]

    portfolio = pd.DataFrame({"total_value": [10000 * (1.01**i) for i in range(12)]}, index=dates)

    benchmark = pd.DataFrame(
        {"benchmark_value": [10000 * (1.005**i) for i in range(12)]}, index=dates
    )

    summary = summarize_performance(portfolio, benchmark, risk_free_rate=0.02)

    assert "total_return" in summary
    assert "cagr" in summary
    assert "sharpe_ratio" in summary
    assert "max_drawdown" in summary
    assert "beta" in summary
    assert "alpha" in summary
    assert "benchmark_return" in summary


def test_handles_negative_returns():
    """Handles portfolios with negative returns."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 9000, 8000]},
        index=[datetime(2020, 1, 1), datetime(2020, 6, 1), datetime(2021, 1, 1)],
    )

    summary = summarize_performance(equity_curve)

    assert summary["total_return"] < 0
    assert summary["cagr"] < 0
    assert summary["max_drawdown"] > 0
