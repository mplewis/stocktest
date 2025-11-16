"""Chart generation using matplotlib."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_equity_curve(
    equity_curve: pd.DataFrame,
    benchmark_curve: pd.DataFrame | None = None,
    output_path: Path | str | None = None,
    title: str = "Portfolio Equity Curve",
) -> None:
    """Plot portfolio equity curve over time.

    Args:
        equity_curve: DataFrame with date index and 'total_value' column
        benchmark_curve: Optional DataFrame with 'benchmark_value' column
        output_path: Optional path to save the chart (PNG/PDF)
        title: Chart title
    """
    if equity_curve.empty or "total_value" not in equity_curve.columns:
        msg = "equity_curve must contain 'total_value' column"
        raise ValueError(msg)

    plt.figure(figsize=(12, 6))

    plt.plot(
        equity_curve.index,
        equity_curve["total_value"],
        label="Portfolio",
        linewidth=2,
        color="#2E86AB",
    )

    if benchmark_curve is not None and not benchmark_curve.empty:
        if "benchmark_value" not in benchmark_curve.columns:
            msg = "benchmark_curve must contain 'benchmark_value' column"
            raise ValueError(msg)

        plt.plot(
            benchmark_curve.index,
            benchmark_curve["benchmark_value"],
            label="Benchmark",
            linewidth=2,
            color="#A23B72",
            linestyle="--",
        )

    plt.title(title, fontsize=14, fontweight="bold")
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Portfolio Value ($)", fontsize=12)
    plt.legend(loc="best", fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


def plot_drawdown(
    equity_curve: pd.DataFrame,
    output_path: Path | str | None = None,
    title: str = "Portfolio Drawdown",
) -> None:
    """Plot portfolio drawdown over time.

    Args:
        equity_curve: DataFrame with date index and 'total_value' column
        output_path: Optional path to save the chart (PNG/PDF)
        title: Chart title
    """
    if equity_curve.empty or "total_value" not in equity_curve.columns:
        msg = "equity_curve must contain 'total_value' column"
        raise ValueError(msg)

    values = equity_curve["total_value"]
    running_max = values.expanding().max()
    drawdown = (values - running_max) / running_max * 100

    plt.figure(figsize=(12, 6))

    plt.fill_between(
        equity_curve.index,
        drawdown,
        0,
        where=(drawdown < 0),
        color="#E63946",
        alpha=0.3,
        label="Drawdown",
    )
    plt.plot(
        equity_curve.index,
        drawdown,
        color="#E63946",
        linewidth=2,
    )

    plt.title(title, fontsize=14, fontweight="bold")
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Drawdown (%)", fontsize=12)
    plt.legend(loc="best", fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.axhline(y=0, color="black", linestyle="-", linewidth=0.8)
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()
    else:
        plt.show()
