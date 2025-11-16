"""Tests for chart generation."""

from datetime import datetime, timedelta

import pandas as pd
import pytest

from stocktest.visualization.charts import plot_drawdown, plot_equity_curve


def test_plots_equity_curve(tmp_path):
    """Plots equity curve and saves to file."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 11000, 12000]},
        index=[datetime(2020, 1, 1), datetime(2020, 6, 1), datetime(2021, 1, 1)],
    )

    output_path = tmp_path / "equity_curve.png"
    plot_equity_curve(equity_curve, output_path=output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plots_equity_curve_with_benchmark(tmp_path):
    """Plots equity curve with benchmark comparison."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 11000, 12000]},
        index=[datetime(2020, 1, 1), datetime(2020, 6, 1), datetime(2021, 1, 1)],
    )

    benchmark_curve = pd.DataFrame(
        {"benchmark_value": [10000, 10500, 11000]},
        index=[datetime(2020, 1, 1), datetime(2020, 6, 1), datetime(2021, 1, 1)],
    )

    output_path = tmp_path / "equity_with_benchmark.png"
    plot_equity_curve(equity_curve, benchmark_curve, output_path=output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_saves_as_pdf(tmp_path):
    """Saves equity curve as PDF."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 11000, 12000]},
        index=[datetime(2020, 1, 1), datetime(2020, 6, 1), datetime(2021, 1, 1)],
    )

    output_path = tmp_path / "equity_curve.pdf"
    plot_equity_curve(equity_curve, output_path=output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_raises_on_missing_total_value_column():
    """Raises ValueError when total_value column is missing."""
    equity_curve = pd.DataFrame(
        {"wrong_column": [10000, 11000]},
        index=[datetime(2020, 1, 1), datetime(2021, 1, 1)],
    )

    with pytest.raises(ValueError, match="must contain 'total_value' column"):
        plot_equity_curve(equity_curve)


def test_raises_on_missing_benchmark_value_column(tmp_path):
    """Raises ValueError when benchmark_value column is missing."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 11000]},
        index=[datetime(2020, 1, 1), datetime(2021, 1, 1)],
    )

    benchmark_curve = pd.DataFrame(
        {"wrong_column": [10000, 10500]},
        index=[datetime(2020, 1, 1), datetime(2021, 1, 1)],
    )

    output_path = tmp_path / "test.png"

    with pytest.raises(ValueError, match="must contain 'benchmark_value' column"):
        plot_equity_curve(equity_curve, benchmark_curve, output_path=output_path)


def test_plots_drawdown(tmp_path):
    """Plots drawdown chart and saves to file."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 12000, 9000, 11000]},
        index=[
            datetime(2020, 1, 1),
            datetime(2020, 2, 1),
            datetime(2020, 3, 1),
            datetime(2020, 4, 1),
        ],
    )

    output_path = tmp_path / "drawdown.png"
    plot_drawdown(equity_curve, output_path=output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plots_drawdown_with_custom_title(tmp_path):
    """Plots drawdown with custom title."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 11000, 12000]},
        index=[datetime(2020, 1, 1), datetime(2020, 6, 1), datetime(2021, 1, 1)],
    )

    output_path = tmp_path / "custom_drawdown.png"
    plot_drawdown(equity_curve, output_path=output_path, title="Custom Drawdown")

    assert output_path.exists()


def test_raises_on_missing_total_value_for_drawdown():
    """Raises ValueError when total_value column is missing."""
    equity_curve = pd.DataFrame(
        {"wrong_column": [10000, 11000]},
        index=[datetime(2020, 1, 1), datetime(2021, 1, 1)],
    )

    with pytest.raises(ValueError, match="must contain 'total_value' column"):
        plot_drawdown(equity_curve)


def test_handles_empty_dataframe_for_equity_curve():
    """Raises ValueError for empty DataFrame."""
    equity_curve = pd.DataFrame()

    with pytest.raises(ValueError, match="must contain 'total_value' column"):
        plot_equity_curve(equity_curve)


def test_handles_empty_dataframe_for_drawdown():
    """Raises ValueError for empty DataFrame."""
    equity_curve = pd.DataFrame()

    with pytest.raises(ValueError, match="must contain 'total_value' column"):
        plot_drawdown(equity_curve)


def test_handles_long_time_series(tmp_path):
    """Handles plotting long time series data."""
    dates = [datetime(2020, 1, 1) + timedelta(days=i) for i in range(365)]
    values = [10000 * (1.001**i) for i in range(365)]

    equity_curve = pd.DataFrame({"total_value": values}, index=dates)

    output_path = tmp_path / "long_series.png"
    plot_equity_curve(equity_curve, output_path=output_path)

    assert output_path.exists()


def test_handles_empty_benchmark_dataframe(tmp_path):
    """Handles empty benchmark DataFrame gracefully."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 11000]},
        index=[datetime(2020, 1, 1), datetime(2021, 1, 1)],
    )

    benchmark_curve = pd.DataFrame()

    output_path = tmp_path / "test.png"
    plot_equity_curve(equity_curve, benchmark_curve, output_path=output_path)

    assert output_path.exists()
