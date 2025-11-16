# Stocktest

A backtesting framework for stock portfolio analysis with intelligent caching and comprehensive performance metrics.

## Features

- **Intelligent Caching**: SQLite-based price data caching with gap detection
- **Flexible Backtesting**: Support for daily, weekly, and monthly rebalancing
- **Comprehensive Metrics**: CAGR, Sharpe ratio, max drawdown, alpha, beta
- **Professional Charts**: Equity curves and drawdown visualizations (matplotlib)
- **CSV Export**: Trade logs, equity curves, and performance summaries
- **Multi-ticker Support**: Equal-weighted or custom portfolio allocations
- **Benchmark Comparison**: Compare against any benchmark ticker

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd stocktest

# Install with uv (recommended)
uv sync --all-extras

# Or install with pip
pip install -e .
```

## Quick Start

### 1. Create a configuration file

Create `config/my_backtest.yaml`:

```yaml
time_periods:
  - name: "2020-2024"
    start_date: "2020-01-01"
    end_date: "2024-12-31"

  - name: "2022-2024"
    start_date: "2022-01-01"
    end_date: "2024-12-31"

tickers:
  - VTI   # Vanguard Total Stock Market ETF
  - BND   # Vanguard Total Bond Market ETF
  - VNQ   # Vanguard Real Estate ETF
```

### 2. Run the backtest

```bash
# Run all time periods
stocktest config/my_backtest.yaml

# Run a specific period
stocktest config/my_backtest.yaml --period "2020-2024"

# Add transaction costs and benchmark
stocktest config/my_backtest.yaml --cost 0.1 --benchmark SPY

# Customize output directory
stocktest config/my_backtest.yaml --output results/
```

### 3. View results

Results are organized by time period:

```
output/
├── 2020-2024/
│   ├── charts/
│   │   ├── equity.png       # Portfolio value over time
│   │   └── drawdown.png     # Drawdown visualization
│   └── data/
│       ├── equity.csv       # Daily portfolio values
│       ├── trades.csv       # Trade log
│       └── summary.csv      # Performance metrics
└── 2022-2024/
    └── ...
```

## Command-Line Options

```
stocktest [-h] [-p PERIOD] [-o OUTPUT] [--db DB] [-c COST] [-b BENCHMARK] config

Positional arguments:
  config                Path to YAML configuration file

Optional arguments:
  -h, --help            Show help message
  -p, --period PERIOD   Time period name to backtest (default: all periods)
  -o, --output OUTPUT   Output directory (default: ./output)
  --db DB               Database path for caching (default: data/stocktest.db)
  -c, --cost COST       Transaction cost percentage (default: 0.0)
  -b, --benchmark BENCHMARK
                        Benchmark ticker for comparison (e.g., SPY)
```

## Python API

### Running a backtest

```python
from datetime import datetime
from stocktest.backtest.engine import run_backtest

result = run_backtest(
    tickers=["VTI", "BND"],
    weights={"VTI": 0.6, "BND": 0.4},
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2024, 12, 31),
    initial_capital=10000.0,
    rebalance_frequency="monthly",
    transaction_cost_pct=0.1,
    benchmark_ticker="SPY",
)

portfolio = result["portfolio"]
equity_curve = result["equity_curve"]
benchmark = result["benchmark"]
```

### Calculating metrics

```python
from stocktest.analysis.metrics import summarize_performance

metrics = summarize_performance(
    equity_curve,
    benchmark_curve=benchmark,
    risk_free_rate=0.02,
)

print(f"CAGR: {metrics['cagr']:.2%}")
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
print(f"Alpha: {metrics['alpha']:.2%}")
```

### Generating visualizations

```python
from stocktest.visualization.charts import plot_equity_curve, plot_drawdown

plot_equity_curve(
    equity_curve,
    benchmark,
    output_path="equity.png",
    title="My Portfolio"
)

plot_drawdown(
    equity_curve,
    output_path="drawdown.png"
)
```

### Exporting data

```python
from stocktest.analysis.reporting import (
    export_equity_curve,
    export_trade_log,
    export_summary_stats,
)

export_equity_curve(equity_curve, "equity.csv")
export_trade_log(portfolio, "trades.csv")
export_summary_stats(metrics, "summary.csv")
```

## Performance Metrics

Stocktest calculates the following metrics:

- **Total Return**: Simple return from initial to final value
- **CAGR**: Compound Annual Growth Rate
- **Sharpe Ratio**: Risk-adjusted returns (annualized)
- **Max Drawdown**: Maximum peak-to-trough decline
- **Beta**: Portfolio volatility relative to benchmark
- **Alpha**: Excess returns over CAPM expectations

## Architecture

### Database Layer

- SQLite database for price data caching
- Alembic migrations for schema management
- Intelligent gap detection and partial cache hits
- Prices stored as integer cents to avoid floating-point errors

### Backtesting Engine

- Portfolio tracking with position management
- Configurable rebalancing frequencies
- Transaction cost modeling
- Benchmark comparison

### Data Fetcher

- yfinance integration with retry logic
- Exponential backoff with jitter
- Rate limiting between requests
- Cache-first retrieval strategy

## Development

### Running tests

```bash
# Run all tests
uv run pytest src/

# Run with coverage
uv run pytest src/ --cov=src/stocktest --cov-report=html

# Run specific test file
uv run pytest src/stocktest/backtest/engine_test.py -v
```

### Linting

```bash
# Check code
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Pre-commit hooks

```bash
# Install hooks
uv run prek install

# Run hooks manually
uv run prek run --all-files
```

## Project Structure

```
stocktest/
├── src/stocktest/
│   ├── analysis/          # Performance metrics and reporting
│   ├── backtest/          # Backtesting engine
│   ├── data/              # Data fetching and caching
│   ├── visualization/     # Chart generation
│   ├── cli.py             # Command-line interface
│   └── config.py          # Configuration schemas
├── alembic/               # Database migrations
├── config/                # Example configurations
├── docs/                  # Documentation
└── tests/                 # Test files (co-located with source)
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
