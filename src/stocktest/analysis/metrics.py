"""Performance metrics for portfolio analysis."""

import numpy as np
import pandas as pd

MIN_DATA_POINTS = 2


def calculate_total_return(equity_curve: pd.DataFrame) -> float:
    """Calculate total return from initial to final value.

    Args:
        equity_curve: DataFrame with 'total_value' column

    Returns:
        Total return as a decimal (0.50 = 50%)
    """
    if equity_curve.empty or "total_value" not in equity_curve.columns:
        return 0.0

    initial_value = equity_curve["total_value"].iloc[0]
    final_value = equity_curve["total_value"].iloc[-1]

    if initial_value == 0:
        return 0.0

    return (final_value - initial_value) / initial_value


def calculate_cagr(equity_curve: pd.DataFrame) -> float:
    """Calculate Compound Annual Growth Rate.

    Args:
        equity_curve: DataFrame with date index and 'total_value' column

    Returns:
        CAGR as a decimal (0.08 = 8% annual growth)
    """
    if equity_curve.empty or "total_value" not in equity_curve.columns:
        return 0.0

    if len(equity_curve) < MIN_DATA_POINTS:
        return 0.0

    initial_value = equity_curve["total_value"].iloc[0]
    final_value = equity_curve["total_value"].iloc[-1]

    if initial_value == 0 or final_value == 0:
        return 0.0

    start_date = equity_curve.index[0]
    end_date = equity_curve.index[-1]
    years = (end_date - start_date).days / 365.25

    if years == 0:
        return 0.0

    return (final_value / initial_value) ** (1 / years) - 1


def calculate_sharpe_ratio(equity_curve: pd.DataFrame, risk_free_rate: float = 0.0) -> float:
    """Calculate Sharpe ratio from daily returns.

    Args:
        equity_curve: DataFrame with 'total_value' column
        risk_free_rate: Annual risk-free rate as decimal (0.02 = 2%)

    Returns:
        Sharpe ratio (annualized)
    """
    if equity_curve.empty or "total_value" not in equity_curve.columns:
        return 0.0

    if len(equity_curve) < MIN_DATA_POINTS:
        return 0.0

    returns = equity_curve["total_value"].pct_change().dropna()

    if len(returns) == 0:
        return 0.0

    mean_return = returns.mean()
    std_return = returns.std()

    if std_return == 0:
        return 0.0

    daily_rf = (1 + risk_free_rate) ** (1 / 252) - 1
    excess_return = mean_return - daily_rf

    sharpe = excess_return / std_return
    return sharpe * np.sqrt(252)


def calculate_max_drawdown(equity_curve: pd.DataFrame) -> float:
    """Calculate maximum drawdown from peak.

    Args:
        equity_curve: DataFrame with 'total_value' column

    Returns:
        Maximum drawdown as a positive decimal (0.20 = 20% drawdown)
    """
    if equity_curve.empty or "total_value" not in equity_curve.columns:
        return 0.0

    values = equity_curve["total_value"]
    running_max = values.expanding().max()
    drawdown = (values - running_max) / running_max

    return abs(drawdown.min())


def calculate_beta(portfolio_curve: pd.DataFrame, benchmark_curve: pd.DataFrame) -> float:
    """Calculate portfolio beta relative to benchmark.

    Args:
        portfolio_curve: DataFrame with 'total_value' column
        benchmark_curve: DataFrame with 'benchmark_value' column

    Returns:
        Beta coefficient (1.0 = same volatility as benchmark)
    """
    if (
        portfolio_curve.empty
        or benchmark_curve.empty
        or "total_value" not in portfolio_curve.columns
        or "benchmark_value" not in benchmark_curve.columns
    ):
        return 0.0

    aligned = pd.merge(
        portfolio_curve[["total_value"]],
        benchmark_curve[["benchmark_value"]],
        left_index=True,
        right_index=True,
        how="inner",
    )

    if len(aligned) < MIN_DATA_POINTS:
        return 0.0

    portfolio_returns = aligned["total_value"].pct_change().dropna()
    benchmark_returns = aligned["benchmark_value"].pct_change().dropna()

    if len(portfolio_returns) < MIN_DATA_POINTS or len(benchmark_returns) < MIN_DATA_POINTS:
        return 0.0

    covariance = np.cov(portfolio_returns, benchmark_returns)[0, 1]
    benchmark_variance = np.var(benchmark_returns)

    if benchmark_variance == 0:
        return 0.0

    return covariance / benchmark_variance


def calculate_alpha(
    portfolio_curve: pd.DataFrame,
    benchmark_curve: pd.DataFrame,
    risk_free_rate: float = 0.0,
) -> float:
    """Calculate portfolio alpha (excess return over CAPM).

    Args:
        portfolio_curve: DataFrame with 'total_value' column
        benchmark_curve: DataFrame with 'benchmark_value' column
        risk_free_rate: Annual risk-free rate as decimal

    Returns:
        Annualized alpha as decimal (0.02 = 2% annual outperformance)
    """
    if (
        portfolio_curve.empty
        or benchmark_curve.empty
        or "total_value" not in portfolio_curve.columns
        or "benchmark_value" not in benchmark_curve.columns
    ):
        return 0.0

    aligned = pd.merge(
        portfolio_curve[["total_value"]],
        benchmark_curve[["benchmark_value"]],
        left_index=True,
        right_index=True,
        how="inner",
    )

    if len(aligned) < MIN_DATA_POINTS:
        return 0.0

    portfolio_returns = aligned["total_value"].pct_change().dropna()
    benchmark_returns = aligned["benchmark_value"].pct_change().dropna()

    if len(portfolio_returns) < MIN_DATA_POINTS or len(benchmark_returns) < MIN_DATA_POINTS:
        return 0.0

    beta = calculate_beta(portfolio_curve, benchmark_curve)
    daily_rf = (1 + risk_free_rate) ** (1 / 252) - 1

    portfolio_mean = portfolio_returns.mean()
    benchmark_mean = benchmark_returns.mean()

    daily_alpha = portfolio_mean - (daily_rf + beta * (benchmark_mean - daily_rf))

    return daily_alpha * 252


def summarize_performance(
    portfolio_curve: pd.DataFrame,
    benchmark_curve: pd.DataFrame | None = None,
    risk_free_rate: float = 0.0,
) -> dict[str, float]:
    """Summarize all performance metrics.

    Args:
        portfolio_curve: DataFrame with 'total_value' column
        benchmark_curve: Optional DataFrame with 'benchmark_value' column
        risk_free_rate: Annual risk-free rate as decimal

    Returns:
        Dictionary of performance metrics
    """
    metrics = {
        "total_return": calculate_total_return(portfolio_curve),
        "cagr": calculate_cagr(portfolio_curve),
        "sharpe_ratio": calculate_sharpe_ratio(portfolio_curve, risk_free_rate),
        "max_drawdown": calculate_max_drawdown(portfolio_curve),
    }

    if benchmark_curve is not None:
        metrics["beta"] = calculate_beta(portfolio_curve, benchmark_curve)
        metrics["alpha"] = calculate_alpha(portfolio_curve, benchmark_curve, risk_free_rate)
        metrics["benchmark_return"] = calculate_total_return(
            benchmark_curve.rename(columns={"benchmark_value": "total_value"})
        )

    return metrics
