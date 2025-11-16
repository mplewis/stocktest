"""Tests for interactive chart generation."""

from pathlib import Path

import pandas as pd
import pytest

from stocktest.visualization.interactive_charts import (
    plot_comparison_interactive,
    plot_drawdown_interactive,
    plot_equity_curve_interactive,
)


def test_plots_equity_curve_interactive(tmp_path):
    """Generates interactive equity curve HTML."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 10500, 11000, 10800]},
        index=pd.date_range("2020-01-01", periods=4),
    )

    output_path = tmp_path / "equity.html"
    html = plot_equity_curve_interactive(equity_curve, output_path=output_path)

    assert output_path.exists()
    assert "Portfolio" in html
    assert "plotly" in html.lower()
    content = output_path.read_text()
    assert "total_value" in content or "Portfolio" in content


def test_plots_equity_curve_interactive_with_benchmark(tmp_path):
    """Generates interactive equity curve with benchmark."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 10500, 11000, 10800]},
        index=pd.date_range("2020-01-01", periods=4),
    )
    benchmark = pd.DataFrame(
        {"total_value": [10000, 10200, 10400, 10600]},
        index=pd.date_range("2020-01-01", periods=4),
    )

    output_path = tmp_path / "equity_bench.html"
    html = plot_equity_curve_interactive(
        equity_curve, output_path=output_path, benchmark_data=benchmark
    )

    assert output_path.exists()
    assert "Portfolio" in html
    assert "Benchmark" in html


def test_returns_html_without_saving(tmp_path):
    """Returns HTML string without saving to file."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 10500, 11000]},
        index=pd.date_range("2020-01-01", periods=3),
    )

    html = plot_equity_curve_interactive(equity_curve, output_path=None)

    assert isinstance(html, str)
    assert "Portfolio" in html
    assert "plotly" in html.lower()


def test_raises_on_empty_equity_curve(tmp_path):
    """Raises ValueError on empty DataFrame."""
    equity_curve = pd.DataFrame()
    output_path = tmp_path / "equity.html"

    with pytest.raises(ValueError, match="empty"):
        plot_equity_curve_interactive(equity_curve, output_path=output_path)


def test_raises_on_missing_total_value_column(tmp_path):
    """Raises ValueError when total_value column is missing."""
    equity_curve = pd.DataFrame(
        {"value": [10000, 10500]}, index=pd.date_range("2020-01-01", periods=2)
    )
    output_path = tmp_path / "equity.html"

    with pytest.raises(ValueError, match="total_value"):
        plot_equity_curve_interactive(equity_curve, output_path=output_path)


def test_plots_drawdown_interactive(tmp_path):
    """Generates interactive drawdown chart HTML."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 10500, 10200, 10800, 10400]},
        index=pd.date_range("2020-01-01", periods=5),
    )

    output_path = tmp_path / "drawdown.html"
    html = plot_drawdown_interactive(equity_curve, output_path=output_path)

    assert output_path.exists()
    assert "Drawdown" in html
    assert "plotly" in html.lower()


def test_plots_drawdown_with_custom_title(tmp_path):
    """Generates drawdown chart with custom title."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 9500, 9000]},
        index=pd.date_range("2020-01-01", periods=3),
    )

    output_path = tmp_path / "drawdown_custom.html"
    html = plot_drawdown_interactive(
        equity_curve, output_path=output_path, title="Custom Drawdown Title"
    )

    assert "Custom Drawdown Title" in html


def test_raises_on_empty_drawdown_input(tmp_path):
    """Raises ValueError on empty DataFrame for drawdown."""
    equity_curve = pd.DataFrame()
    output_path = tmp_path / "drawdown.html"

    with pytest.raises(ValueError, match="empty"):
        plot_drawdown_interactive(equity_curve, output_path=output_path)


def test_plots_comparison_interactive(tmp_path):
    """Generates interactive comparison chart HTML."""
    results = {
        "AAPL": {
            "equity_curve": pd.DataFrame(
                {"total_value": [10000, 10500, 11000]},
                index=pd.date_range("2020-01-01", periods=3),
            )
        },
        "GOOGL": {
            "equity_curve": pd.DataFrame(
                {"total_value": [10000, 10200, 10800]},
                index=pd.date_range("2020-01-01", periods=3),
            )
        },
    }

    output_path = tmp_path / "comparison.html"
    html = plot_comparison_interactive(results, output_path=output_path)

    assert output_path.exists()
    assert "AAPL" in html
    assert "GOOGL" in html
    assert "plotly" in html.lower()


def test_comparison_handles_single_ticker(tmp_path):
    """Handles comparison with only one ticker."""
    results = {
        "TSLA": {
            "equity_curve": pd.DataFrame(
                {"total_value": [10000, 11000, 12000]},
                index=pd.date_range("2020-01-01", periods=3),
            )
        }
    }

    output_path = tmp_path / "comparison_single.html"
    html = plot_comparison_interactive(results, output_path=output_path)

    assert output_path.exists()
    assert "TSLA" in html


def test_comparison_raises_on_empty_results(tmp_path):
    """Raises ValueError on empty results dictionary."""
    results = {}
    output_path = tmp_path / "comparison.html"

    with pytest.raises(ValueError, match="empty"):
        plot_comparison_interactive(results, output_path=output_path)


def test_comparison_skips_invalid_equity_curves(tmp_path):
    """Skips tickers with invalid equity curves."""
    results = {
        "VALID": {
            "equity_curve": pd.DataFrame(
                {"total_value": [10000, 11000]},
                index=pd.date_range("2020-01-01", periods=2),
            )
        },
        "EMPTY": {"equity_curve": pd.DataFrame()},
        "NO_COLUMN": {
            "equity_curve": pd.DataFrame(
                {"value": [10000, 11000]}, index=pd.date_range("2020-01-01", periods=2)
            )
        },
    }

    output_path = tmp_path / "comparison_partial.html"
    html = plot_comparison_interactive(results, output_path=output_path)

    assert output_path.exists()
    assert "VALID" in html
    assert "EMPTY" not in html
    assert "NO_COLUMN" not in html


def test_creates_parent_directories(tmp_path):
    """Creates parent directories if they don't exist."""
    output_path = tmp_path / "nested" / "path" / "equity.html"
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 11000]}, index=pd.date_range("2020-01-01", periods=2)
    )

    plot_equity_curve_interactive(equity_curve, output_path=output_path)

    assert output_path.exists()
    assert output_path.parent.exists()


def test_handles_pathlib_and_string_paths(tmp_path):
    """Accepts both Path and string for output_path."""
    equity_curve = pd.DataFrame(
        {"total_value": [10000, 11000]}, index=pd.date_range("2020-01-01", periods=2)
    )

    path_obj = tmp_path / "equity_path.html"
    plot_equity_curve_interactive(equity_curve, output_path=path_obj)
    assert path_obj.exists()

    path_str = str(tmp_path / "equity_str.html")
    plot_equity_curve_interactive(equity_curve, output_path=path_str)
    assert Path(path_str).exists()
