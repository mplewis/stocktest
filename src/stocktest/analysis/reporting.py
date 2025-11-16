"""Reporting and export functionality."""

from pathlib import Path

import pandas as pd

from stocktest.backtest.engine import Portfolio


def export_equity_curve(equity_curve: pd.DataFrame, output_path: Path | str) -> None:
    """Export daily portfolio values to CSV.

    Args:
        equity_curve: DataFrame with date index and portfolio values
        output_path: Path to save CSV file
    """
    if equity_curve.empty:
        msg = "equity_curve cannot be empty"
        raise ValueError(msg)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    equity_curve.to_csv(output_path, index=True)


def export_trade_log(portfolio: Portfolio, output_path: Path | str) -> None:
    """Export trade log to CSV.

    Args:
        portfolio: Portfolio object with trade history
        output_path: Path to save CSV file
    """
    if not portfolio.history:
        msg = "portfolio has no trade history"
        raise ValueError(msg)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    trades_data = []
    for entry in portfolio.history:
        date = entry["date"]
        for trade in entry.get("trades", []):
            trades_data.append(
                {
                    "date": date,
                    "ticker": trade["ticker"],
                    "shares": trade["shares"],
                    "price": trade["price"],
                    "value": trade["value"],
                    "transaction_cost": trade["cost"],
                }
            )

    if not trades_data:
        msg = "no trades found in portfolio history"
        raise ValueError(msg)

    df = pd.DataFrame(trades_data)
    df.to_csv(output_path, index=False)


def export_summary_stats(metrics: dict[str, float], output_path: Path | str) -> None:
    """Export summary statistics to CSV.

    Args:
        metrics: Dictionary of performance metrics
        output_path: Path to save CSV file
    """
    if not metrics:
        msg = "metrics dictionary cannot be empty"
        raise ValueError(msg)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame([{"metric": key, "value": value} for key, value in metrics.items()])
    df.to_csv(output_path, index=False)


def create_report_directory(base_path: Path | str, report_name: str) -> Path:
    """Create directory structure for reports.

    Args:
        base_path: Base output directory
        report_name: Name of the report

    Returns:
        Path to the created report directory
    """
    base_path = Path(base_path)
    report_path = base_path / report_name
    report_path.mkdir(parents=True, exist_ok=True)

    (report_path / "charts").mkdir(exist_ok=True)
    (report_path / "data").mkdir(exist_ok=True)

    return report_path
