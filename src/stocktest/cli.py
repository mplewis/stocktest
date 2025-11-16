"""CLI for comparing individual ticker performance."""

import argparse
import sys
import traceback
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import yaml

from stocktest.analysis.metrics import summarize_performance
from stocktest.analysis.reporting import create_report_directory
from stocktest.backtest.engine import BacktestConfig, run_backtest
from stocktest.config import Config


def _create_comparison_chart(results, period, report_path):
    """Create comparison chart for multiple tickers.

    Args:
        results: Dictionary mapping ticker to backtest results
        period: TimePeriod configuration
        report_path: Path to save chart

    Returns:
        Path to saved chart
    """
    plt.figure(figsize=(14, 8))

    for ticker, result in results.items():
        equity_curve = result["equity_curve"]
        normalized = equity_curve["total_value"] / equity_curve["total_value"].iloc[0] * 100
        plt.plot(equity_curve.index, normalized, label=ticker, linewidth=2)

    plt.title(
        f"Portfolio Performance Comparison - {period.name}",
        fontsize=14,
        fontweight="bold",
    )
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Portfolio Value (Initial = 100)", fontsize=12)
    plt.legend(loc="best", fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    chart_path = report_path / "comparison.png"
    plt.savefig(chart_path, dpi=300, bbox_inches="tight")
    plt.close()

    return chart_path


def _print_results_summary(metrics_df):
    """Print formatted results summary.

    Args:
        metrics_df: DataFrame with performance metrics
    """
    print("\n  Results Summary:")
    print("  ================")
    for _, row in metrics_df.iterrows():
        print(
            f"  {row['ticker']:8s} - Return: {row['total_return']:7.2%}  "
            f"CAGR: {row['cagr']:7.2%}  Sharpe: {row['sharpe_ratio']:5.2f}  "
            f"Max DD: {row['max_drawdown']:7.2%}"
        )


def run_comparison_backtest(
    config: Config,
    period_name: str,
    output_dir: Path,
    db_path: Path | None = None,
    transaction_cost: float = 0.0,
) -> None:
    """Run backtests for each ticker individually and compare.

    Args:
        config: Configuration object
        period_name: Name of time period to backtest
        output_dir: Directory for output files
        db_path: Optional database path for caching
        transaction_cost: Transaction cost percentage
    """
    period = next((p for p in config.time_periods if p.name == period_name), None)
    if not period:
        msg = f"Period '{period_name}' not found in config"
        raise ValueError(msg)

    print(f"Running comparison backtest for {period.name}...")
    print(f"  Period: {period.start_date.date()} to {period.end_date.date()}")
    print(f"  Tickers: {', '.join(config.tickers)}")
    print("  Strategy: 100% allocation per ticker\n")

    report_path = create_report_directory(output_dir, period.name)
    results = {}
    all_metrics = []

    for ticker in config.tickers:
        print(f"  Backtesting {ticker}...")

        try:
            backtest_config = BacktestConfig(
                tickers=[ticker],
                weights={ticker: 1.0},
                start_date=period.start_date,
                end_date=period.end_date,
                transaction_cost_pct=transaction_cost,
                db_path=str(db_path) if db_path else None,
            )
            result = run_backtest(backtest_config)

            metrics = summarize_performance(result["equity_curve"])
            metrics["ticker"] = ticker
            all_metrics.append(metrics)

            results[ticker] = result

            print(f"    Total Return: {metrics['total_return']:.2%}")
            print(f"    CAGR: {metrics['cagr']:.2%}")
            print(f"    Sharpe: {metrics['sharpe_ratio']:.2f}")
            print(f"    Max DD: {metrics['max_drawdown']:.2%}")

        except Exception as e:
            print(f"    Error: {e}")
            continue

    if not all_metrics:
        print("\n  Error: No tickers had valid data for this period")
        return

    print("\n  Creating comparison chart...")
    chart_path = _create_comparison_chart(results, period, report_path)

    metrics_df = pd.DataFrame(all_metrics)
    metrics_df = metrics_df.sort_values("total_return", ascending=False)
    summary_path = report_path / "comparison_summary.csv"
    metrics_df.to_csv(summary_path, index=False)

    _print_results_summary(metrics_df)

    print(f"\n  Chart saved: {chart_path}")
    print(f"  Summary saved: {summary_path}")


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point.

    Args:
        argv: Command line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Compare individual ticker performance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "config",
        type=Path,
        help="Path to YAML configuration file",
    )

    parser.add_argument(
        "-p",
        "--period",
        help="Time period name to backtest (default: all periods)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output/comparisons"),
        help="Output directory (default: ./output/comparisons)",
    )

    parser.add_argument(
        "--db",
        type=Path,
        help="Database path for caching (default: data/stocktest.db)",
    )

    parser.add_argument(
        "-c",
        "--cost",
        type=float,
        default=0.0,
        help="Transaction cost percentage (default: 0.0)",
    )

    args = parser.parse_args(argv)

    try:
        with open(args.config) as f:
            data = yaml.safe_load(f)
        config = Config(**data)

        db_path = args.db if args.db else Path("data/stocktest.db")

        if args.period:
            run_comparison_backtest(
                config,
                args.period,
                args.output,
                db_path,
                args.cost,
            )
        else:
            for period in config.time_periods:
                run_comparison_backtest(
                    config,
                    period.name,
                    args.output,
                    db_path,
                    args.cost,
                )
                print()

        print("\nComparison backtest completed successfully!")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
