"""CLI for comparing individual ticker performance."""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import structlog
import yaml

from stocktest.analysis.metrics import summarize_performance
from stocktest.analysis.reporting import create_report_directory
from stocktest.backtest.engine import BacktestConfig, run_backtest
from stocktest.config import Config
from stocktest.data.fetcher import fetch_multiple_tickers
from stocktest.logging import configure_logging

logger = structlog.get_logger()


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
    """Log formatted results summary.

    Args:
        metrics_df: DataFrame with performance metrics
    """
    logger.info("results summary")
    for _, row in metrics_df.iterrows():
        logger.info(
            "ticker performance",
            ticker=row["ticker"],
            total_return=row["total_return"],
            cagr=row["cagr"],
            sharpe_ratio=row["sharpe_ratio"],
            max_drawdown=row["max_drawdown"],
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

    logger.info(
        "starting comparison backtest",
        period_name=period.name,
        start_date=str(period.start_date.date()),
        end_date=str(period.end_date.date()),
        tickers=config.tickers,
        strategy="100% allocation per ticker",
    )

    logger.info("pre-fetching price data for all tickers", ticker_count=len(config.tickers))
    fetch_multiple_tickers(
        config.tickers,
        period.start_date,
        period.end_date,
        str(db_path) if db_path else None,
    )

    report_path = create_report_directory(output_dir, period.name)
    results = {}
    all_metrics = []

    for ticker in config.tickers:
        logger.info("backtesting ticker", ticker=ticker, status="started")

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

            logger.info(
                "backtest completed for ticker",
                ticker=ticker,
                total_return=metrics["total_return"],
                cagr=metrics["cagr"],
                sharpe_ratio=metrics["sharpe_ratio"],
                max_drawdown=metrics["max_drawdown"],
            )

        except Exception as e:
            logger.warning("backtest failed for ticker", ticker=ticker, error=str(e))
            continue

    if not all_metrics:
        logger.error("no tickers had valid data for period", period_name=period.name)
        return

    logger.info("creating comparison chart", period_name=period.name)
    chart_path = _create_comparison_chart(results, period, report_path)

    metrics_df = pd.DataFrame(all_metrics)
    metrics_df = metrics_df.sort_values("total_return", ascending=False)
    summary_path = report_path / "comparison_summary.csv"
    metrics_df.to_csv(summary_path, index=False)

    _print_results_summary(metrics_df)

    logger.info(
        "comparison backtest complete",
        chart_path=str(chart_path),
        summary_path=str(summary_path),
    )


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point.

    Args:
        argv: Command line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    configure_logging()

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

        logger.info("all comparison backtests completed successfully")
        return 0

    except Exception as e:
        logger.error("comparison backtest failed", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
