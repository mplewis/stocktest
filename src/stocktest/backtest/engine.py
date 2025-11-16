"""Backtesting engine for portfolio simulation."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd

from stocktest.data.fetcher import fetch_price_data

MIN_TRADE_VALUE = 0.01
WEIGHT_TOLERANCE = 0.001


@dataclass
class BacktestConfig:
    """Configuration for backtest execution."""

    tickers: list[str]
    weights: dict[str, float]
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10000.0
    rebalance_frequency: str = "monthly"
    transaction_cost_pct: float = 0.0
    benchmark_ticker: str | None = None
    db_path: str | None = None


class Portfolio:
    """Portfolio tracker with position management and transaction costs."""

    def __init__(
        self,
        initial_capital: float,
        transaction_cost_pct: float = 0.0,
        db_path: str | None = None,
    ):
        """Initialize portfolio with starting capital.

        Args:
            initial_capital: Starting cash amount in dollars
            transaction_cost_pct: Transaction cost as percentage (0.1 = 0.1%)
            db_path: Optional database path for caching
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.db_path = db_path
        self.positions: dict[str, float] = {}
        self.history: list[dict[str, Any]] = []

    def get_position_value(self, ticker: str, price: float) -> float:
        """Get current value of a position.

        Args:
            ticker: Stock ticker symbol
            price: Current price per share

        Returns:
            Total value of position in dollars
        """
        return self.positions.get(ticker, 0.0) * price

    def get_total_value(self, prices: dict[str, float]) -> float:
        """Calculate total portfolio value.

        Args:
            prices: Dictionary mapping tickers to current prices

        Returns:
            Total portfolio value (cash + positions)
        """
        position_value = sum(
            self.get_position_value(ticker, prices[ticker])
            for ticker in self.positions
            if ticker in prices
        )
        return self.cash + position_value

    def calculate_transaction_cost(self, amount: float) -> float:
        """Calculate transaction cost for a trade.

        Args:
            amount: Dollar amount of the trade

        Returns:
            Transaction cost in dollars
        """
        return abs(amount) * (self.transaction_cost_pct / 100.0)

    def rebalance(
        self, target_weights: dict[str, float], prices: dict[str, float], date: datetime
    ) -> None:
        """Rebalance portfolio to target weights.

        Args:
            target_weights: Dictionary mapping tickers to target weight (0-1)
            prices: Dictionary mapping tickers to current prices
            date: Current date for history tracking
        """
        total_value = self.get_total_value(prices)
        target_values = {ticker: total_value * weight for ticker, weight in target_weights.items()}
        trades = []

        for ticker, target_value in target_values.items():
            if ticker not in prices:
                continue

            current_shares = self.positions.get(ticker, 0.0)
            current_value = current_shares * prices[ticker]
            trade_value = target_value - current_value

            if abs(trade_value) < MIN_TRADE_VALUE:
                continue

            transaction_cost = self.calculate_transaction_cost(trade_value)
            shares_to_trade = trade_value / prices[ticker]

            self.positions[ticker] = self.positions.get(ticker, 0.0) + shares_to_trade
            self.cash -= trade_value + transaction_cost

            trades.append(
                {
                    "ticker": ticker,
                    "shares": shares_to_trade,
                    "price": prices[ticker],
                    "value": trade_value,
                    "cost": transaction_cost,
                }
            )

        self.history.append(
            {
                "date": date,
                "total_value": self.get_total_value(prices),
                "cash": self.cash,
                "positions": dict(self.positions),
                "trades": trades,
            }
        )

    def get_equity_curve(self) -> pd.DataFrame:
        """Get portfolio value over time.

        Returns:
            DataFrame with date index and portfolio values
        """
        if not self.history:
            return pd.DataFrame()

        data = {
            "date": [h["date"] for h in self.history],
            "total_value": [h["total_value"] for h in self.history],
            "cash": [h["cash"] for h in self.history],
        }

        return pd.DataFrame(data).set_index("date")


def run_backtest(config: BacktestConfig) -> dict[str, Any]:
    """Run a backtest with rebalancing.

    Args:
        config: BacktestConfig with all backtest parameters

    Returns:
        Dictionary containing portfolio, equity curve, and benchmark data
    """
    if abs(sum(config.weights.values()) - 1.0) > WEIGHT_TOLERANCE:
        msg = f"Weights must sum to 1.0, got {sum(config.weights.values())}"
        raise ValueError(msg)

    portfolio = Portfolio(config.initial_capital, config.transaction_cost_pct, config.db_path)
    price_data = {}

    for ticker in config.tickers:
        df = fetch_price_data(ticker, config.start_date, config.end_date, config.db_path)
        if df is not None and not df.empty:
            price_data[ticker] = df

    if not price_data:
        msg = "No price data available for any tickers"
        raise ValueError(msg)

    all_dates = pd.DatetimeIndex(sorted(set().union(*[df.index for df in price_data.values()])))

    rebalance_dates = _get_rebalance_dates(all_dates, config.rebalance_frequency)

    for date in all_dates:
        prices = {}
        for ticker, df in price_data.items():
            if date in df.index:
                prices[ticker] = df.loc[date, "Close"]
            elif len(df[df.index <= date]) > 0:
                prices[ticker] = df[df.index <= date].iloc[-1]["Close"]

        if not prices:
            continue

        if date in rebalance_dates:
            portfolio.rebalance(config.weights, prices, date)

    result: dict[str, Any] = {
        "portfolio": portfolio,
        "equity_curve": portfolio.get_equity_curve(),
    }

    if config.benchmark_ticker:
        benchmark_data = fetch_price_data(
            config.benchmark_ticker, config.start_date, config.end_date, config.db_path
        )
        if benchmark_data is not None and not benchmark_data.empty:
            initial_price = benchmark_data.iloc[0]["Close"]
            benchmark_shares = config.initial_capital / initial_price
            benchmark_data["benchmark_value"] = benchmark_data["Close"] * benchmark_shares
            result["benchmark"] = benchmark_data[["benchmark_value"]]

    return result


def _get_rebalance_dates(all_dates: pd.DatetimeIndex, frequency: str) -> set[pd.Timestamp]:
    """Get rebalancing dates based on frequency.

    Args:
        all_dates: All available trading dates
        frequency: Rebalancing frequency ('daily', 'weekly', 'monthly')

    Returns:
        Set of dates to rebalance on
    """
    if frequency == "daily":
        return set(all_dates)
    if frequency == "weekly":
        rebalance = set()
        current_week = None
        for date in all_dates:
            week = date.isocalendar()[1]
            if week != current_week:
                rebalance.add(date)
                current_week = week
        return rebalance
    if frequency == "monthly":
        rebalance = set()
        current_month = None
        for date in all_dates:
            month = (date.year, date.month)
            if month != current_month:
                rebalance.add(date)
                current_month = month
        return rebalance
    msg = f"Unknown rebalance frequency: {frequency}"
    raise ValueError(msg)
