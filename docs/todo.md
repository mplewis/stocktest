# Stocktest Implementation Checklist

**Instructions for Future Agent:**

- Work through each section in order from top to bottom
- After completing each task, change `- [ ]` to `- [x]` to mark it as done
- This helps track progress and ensures nothing is missed
- Run tests frequently to catch issues early

## Project Setup

- [x] Create project directory structure (src-layout with src/stocktest/, data/,
      config/, output/)
- [x] Create .gitignore file
- [x] Write pyproject.toml with all dependencies and tool configurations (ruff,
      pytest, coverage, sqlalchemy, alembic)
- [x] Initialize uv project and sync dependencies (uv sync --all-extras)
- [x] Initialize git repository
- [x] Install and configure prek pre-commit hooks
- [x] Create .pre-commit-config.yaml with ruff hooks

## Configuration Layer

- [x] Create src/stocktest/**init**.py
- [x] Create src/stocktest/config_test.py for config tests (next to source file)
- [x] Implement Pydantic config schemas in src/stocktest/config.py (TimePeriod,
      Config)
- [x] Define TimePeriod model with name, start_date, end_date fields and date
      validator
- [x] Define Config model with time_periods and tickers lists
- [x] Add field validator for ticker normalization (uppercase, strip)
- [x] Create config/default.yaml with simple matrix of time periods and tickers
- [x] Write YAML config loader function with Pydantic validation
- [x] Write test for valid configuration loading in config_test.py
- [x] Write test for invalid date range validation in config_test.py
- [x] Write test for ticker normalization in config_test.py
- [x] Write test for empty tickers/periods validation in config_test.py

## Database Layer - SQLAlchemy + Alembic

- [x] Create src/stocktest/data/**init**.py
- [x] Create src/stocktest/data/models.py with SQLAlchemy ORM models (Security,
      Price, CacheMetadata)
- [x] Define Security model with ticker, name, asset_type, created_at,
      updated_at fields
- [x] Define Price model with security_id, timestamp, open, high, low, close,
      volume, adjusted_close (as integers for cents)
- [x] Define CacheMetadata model with security_id, last_fetch, earliest_data,
      latest_data, total_records
- [x] Create src/stocktest/data/database.py with engine and session management
- [x] Implement get_engine function to create SQLAlchemy engine
- [x] Implement get_session context manager for database sessions
- [x] Create src/stocktest/data/database_test.py for database tests
- [x] Write test for engine creation in database_test.py
- [x] Write test for session context manager in database_test.py
- [x] Initialize Alembic for database migrations (alembic init alembic)
- [x] Configure alembic.ini with SQLite database path
- [x] Update alembic/env.py to import models and set target_metadata
- [x] Create initial migration with alembic revision --autogenerate -m "Initial
      schema"
- [x] Create src/stocktest/data/cache.py for cache operations using SQLAlchemy
      ORM
- [x] Create src/stocktest/data/cache_test.py for cache tests
- [x] Write function to get or create security by ticker
- [x] Write function to cache price data using bulk_insert_mappings (convert to
      integer cents)
- [x] Write function to load price data from cache using queries (convert back
      to floats)
- [x] Write function to check cache metadata and find missing date ranges using
      SQLAlchemy queries
- [x] Write function to update cache metadata after successful fetch using ORM
- [x] Write test for get or create security in cache_test.py
- [x] Write test for caching price data in cache_test.py
- [x] Write test for loading price data from cache in cache_test.py
- [x] Write test for gap detection in cache_test.py
- [x] Write test for updating cache metadata in cache_test.py

## Data Layer - yfinance Fetcher

- [x] Create src/stocktest/data/fetcher.py
- [x] Create src/stocktest/data/fetcher_test.py for fetcher tests (with mocked
      yfinance)
- [x] Implement exponential backoff with jitter retry decorator
- [x] Write fetch_with_retry function for yfinance API calls
- [x] Implement cache-first data retrieval function (check cache → find gaps →
      fetch missing → save → return)
- [x] Add delay logic between multiple ticker requests to avoid rate limiting
- [x] Write function to fetch multiple tickers with proper spacing
- [x] Write test for retry logic with exponential backoff in fetcher_test.py
- [x] Write test for cache-first retrieval in fetcher_test.py
- [x] Write test for rate limiting delays in fetcher_test.py

## Backtesting Engine

- [ ] Create src/stocktest/backtest/**init**.py
- [ ] Create src/stocktest/backtest/engine.py
- [ ] Create src/stocktest/backtest/engine_test.py for engine tests
- [ ] Implement Portfolio class to track positions and cash
- [ ] Write function to calculate transaction costs (commission + slippage)
- [ ] Implement backtesting loop (iterate through dates, execute trades, update
      portfolio)
- [ ] Write function to calculate portfolio value at each timestamp
- [ ] Add benchmark comparison logic
- [ ] Write test for portfolio initialization in engine_test.py
- [ ] Write test for transaction cost calculation in engine_test.py
- [ ] Write test for simple buy-and-hold backtest in engine_test.py
- [ ] Write test for benchmark comparison in engine_test.py

## Analysis Layer

- [ ] Create src/stocktest/analysis/**init**.py
- [ ] Create src/stocktest/analysis/metrics.py
- [ ] Create src/stocktest/analysis/metrics_test.py for metrics tests
- [ ] Implement total return calculation
- [ ] Implement CAGR (Compound Annual Growth Rate) calculation
- [ ] Implement Sharpe ratio calculation
- [ ] Implement maximum drawdown calculation
- [ ] Implement benchmark-relative metrics (alpha, beta)
- [ ] Write summary statistics aggregation function
- [ ] Write test for return calculations in metrics_test.py
- [ ] Write test for CAGR calculation in metrics_test.py
- [ ] Write test for Sharpe ratio in metrics_test.py
- [ ] Write test for maximum drawdown in metrics_test.py

## Visualization Layer

- [ ] Create src/stocktest/visualization/**init**.py
- [ ] Create src/stocktest/visualization/charts.py
- [ ] Create src/stocktest/visualization/charts_test.py for chart tests
- [ ] Implement matplotlib equity curve chart (static PNG/PDF)
- [ ] Implement matplotlib drawdown chart
- [ ] Write test for matplotlib chart generation in charts_test.py

## Reporting & Export

- [ ] Create src/stocktest/analysis/reporting.py
- [ ] Create src/stocktest/analysis/reporting_test.py for reporting tests
- [ ] Write function to export daily portfolio values to CSV
- [ ] Write function to export trade log to CSV
- [ ] Write function to export summary statistics to CSV
- [ ] Implement report directory structure creation
- [ ] Write test for CSV export in reporting_test.py

## Integration Tests

- [ ] Create src/stocktest/integration_test.py for end-to-end tests
- [ ] Write end-to-end test: config → fetch → cache → backtest → analyze →
      export
- [ ] Write test for handling yfinance rate limit errors
- [ ] Write test for partial cache hits (some data cached, some needs fetching)
- [ ] Write test for matrix backtest expansion (all time periods x all tickers)

## CLI & Documentation

- [ ] Create src/stocktest/cli.py with argparse or click
- [ ] Implement main function to run backtests from command line
- [ ] Add entry point to pyproject.toml
- [ ] Create README.md with installation instructions
- [ ] Add usage examples to README
- [ ] Document configuration file format
- [ ] Create example Jupyter notebook (notebooks/example_backtest.ipynb)

## Final Polish

- [ ] Run ruff format on all files
- [ ] Run ruff check and fix all linting issues
- [ ] Run pytest with coverage and ensure >80% coverage
- [ ] Run prek on all files to verify pre-commit hooks pass
- [ ] Create sample output (CSV files and charts) for demonstration

---

## Key Implementation Notes for Future Agent

### Project Architecture

- Use **src-layout** (src/stocktest/) to prevent import conflicts
- Store prices as **integer cents** in SQLite to avoid floating-point errors
- Implement **cache-first** strategy for all data fetches

### Critical yfinance Considerations

- yfinance has unofficial rate limits (~60 requests/minute)
- Implement **exponential backoff with jitter** for retries
- Add **delays between ticker requests** (0.5-1 second minimum)
- **Never re-fetch** data that's already cached
- Prefer **Vanguard ETFs** (VTI, VOO, VEA) over mutual funds (VTSAX, VFIAX) for
  better data availability

### SQLAlchemy ORM Models

Use SQLAlchemy 2.0 declarative style with type annotations:

```python
from sqlalchemy import Integer, String, BigInteger, ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime

class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass

class Security(Base):
    """Security/ticker information."""
    __tablename__ = "securities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String)
    asset_type: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False)

    prices: Mapped[list["Price"]] = relationship("Price", back_populates="security")
    cache_metadata: Mapped["CacheMetadata"] = relationship("CacheMetadata", back_populates="security", uselist=False)

class Price(Base):
    """Price data (stored as integer cents to avoid float errors)."""
    __tablename__ = "prices"

    security_id: Mapped[int] = mapped_column(ForeignKey("securities.id"), primary_key=True)
    timestamp: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    open: Mapped[int] = mapped_column(BigInteger, nullable=False)
    high: Mapped[int] = mapped_column(BigInteger, nullable=False)
    low: Mapped[int] = mapped_column(BigInteger, nullable=False)
    close: Mapped[int] = mapped_column(BigInteger, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    adjusted_close: Mapped[int | None] = mapped_column(BigInteger)

    security: Mapped["Security"] = relationship("Security", back_populates="prices")

    __table_args__ = (
        Index("idx_prices_timestamp", "timestamp"),
        Index("idx_prices_security_time", "security_id", "timestamp"),
    )

class CacheMetadata(Base):
    """Cache metadata for tracking data freshness."""
    __tablename__ = "cache_metadata"

    security_id: Mapped[int] = mapped_column(ForeignKey("securities.id"), primary_key=True)
    last_fetch: Mapped[int] = mapped_column(BigInteger, nullable=False)
    earliest_data: Mapped[int | None] = mapped_column(BigInteger)
    latest_data: Mapped[int | None] = mapped_column(BigInteger)
    total_records: Mapped[int | None] = mapped_column(Integer)

    security: Mapped["Security"] = relationship("Security", back_populates="cache_metadata")
```

**Key SQLAlchemy Design Decisions:**

- Use SQLAlchemy 2.0 declarative style with `Mapped` type hints
- Store prices as `BigInteger` (cents) to avoid floating-point errors
- Use composite primary key on Price (security_id, timestamp)
- Define relationships between models for easy querying
- Create indexes on frequently queried columns
- Store timestamps as Unix timestamps (integers)

### Pydantic Configuration Structure

Simple matrix-based configuration for running backtests across all combinations
of time periods and tickers:

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class TimePeriod(BaseModel):
    """Named time period for backtesting."""
    name: str = Field(min_length=1)
    start_date: datetime
    end_date: datetime

    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, v: datetime, info) -> datetime:
        """Ensure end_date > start_date."""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError("end_date must be after start_date")
        return v

class Config(BaseModel):
    """Root configuration for stocktest."""
    time_periods: list[TimePeriod] = Field(min_length=1)
    tickers: list[str] = Field(min_length=1)

    @field_validator('tickers')
    @classmethod
    def normalize_tickers(cls, v: list[str]) -> list[str]:
        """Normalize ticker symbols to uppercase."""
        return [ticker.upper().strip() for ticker in v]
```

The backtest engine will automatically expand this into a matrix:

- If you have 3 time periods and 4 tickers, it will run 12 backtests (3 × 4)
- Each backtest runs one ticker for one time period
- Results are aggregated and compared across the matrix

### Tool Configuration (pyproject.toml)

**Ruff:**

```toml
[tool.ruff]
line-length = 88
target-version = "py39"
src = ["src"]

[tool.ruff.lint]
select = ["E", "F", "B", "I", "UP", "D", "SIM", "PL"]
ignore = ["D100", "D104"]

[tool.ruff.lint.pydocstyle]
convention = "google"
```

**Pytest:**

```toml
[tool.pytest.ini_options]
testpaths = ["src"]  # Tests are co-located with source files
python_files = "*_test.py"  # Test files named module_test.py
python_functions = "test_*"
addopts = "-v --strict-markers --cov=src/stocktest --cov-report=html --cov-report=term-missing"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
]
```

### Dependencies

**Package Manager:**

- Use **uv** for all dependency management and installation
- Run `uv sync --all-extras` to install all dependencies including dev tools
- uv is faster and more reliable than pip

**Core:**

- yfinance>=0.2.40 (Yahoo Finance data)
- pandas>=2.0.0 (data manipulation)
- numpy>=1.24.0 (numerical operations)
- pydantic>=2.0.0 (config schemas)
- pyyaml>=6.0 (YAML configs)
- matplotlib>=3.7.0 (static charts)
- sqlalchemy>=2.0.0 (ORM for database)
- alembic>=1.13.0 (database migrations)

**Dev:**

- ruff>=0.1.8 (linting/formatting)
- pytest>=7.4.0 (testing)
- pytest-cov>=4.1.0 (coverage)
- prek>=0.1.0 (fast pre-commit alternative)

### Visualization Strategy

Generate **matplotlib** charts only:

- **matplotlib**: Static PNG/PDF for reports, publications
- Focus on equity curves and drawdown charts

### Testing Strategy

**Co-located Test Structure:**

- Tests live next to the code they test (not in a separate tests/ directory)
- Test files are named `{module}_test.py` (e.g., `config.py` → `config_test.py`)
- This makes it easy to find tests and keeps related code together
- Pytest will discover all `*_test.py` files in the `src/` directory

**Test Structure:**

```
src/stocktest/
├── config.py
├── config_test.py          # Tests for config.py
├── data/
│   ├── models.py
│   ├── database.py
│   ├── database_test.py    # Tests for database.py
│   ├── cache.py
│   ├── cache_test.py       # Tests for cache.py
│   ├── fetcher.py
│   └── fetcher_test.py     # Tests for fetcher.py
├── backtest/
│   ├── engine.py
│   └── engine_test.py      # Tests for engine.py
└── integration_test.py     # End-to-end integration tests
```

**Test Types:**

1. **Unit tests**: Test individual functions with mocked data (in `*_test.py`
   files)
2. **Integration tests**: Test database ops and API calls (in
   `integration_test.py`)
3. **End-to-end tests**: Full backtest runs with known outcomes (in
   `integration_test.py`)
4. Use **pytest fixtures** in `conftest.py` at package root for shared test data
5. **Mock yfinance** responses in tests to avoid API calls (use `unittest.mock`
   or `pytest-mock`)

### Error Handling

- Catch `RateLimitError` and fall back to cached data
- Validate all configs at load time with Pydantic
- Use context managers for all database connections
- Log warnings for missing data, errors for failures

### User Instructions (from CLAUDE.md)

- Add docstrings to all classes, functions, and top-level constants
- Don't add code comments inside functions
- Never use inline imports (imports at top of file)
- Test format: "it X" not "it should X"
- Package installation: Use `<manager> install <package>` to get latest version

### Example Config (config/default.yaml)

Simple matrix configuration - just tickers and time periods:

```yaml
tickers:
  - VTI # Vanguard Total Stock Market ETF
  - VOO # Vanguard S&P 500 ETF
  - VEA # Vanguard FTSE Developed Markets ETF
  - BND # Vanguard Total Bond Market ETF

time_periods:
  - name: "Pre-COVID"
    start_date: "2018-01-01"
    end_date: "2020-02-01"

  - name: "COVID Era"
    start_date: "2020-03-01"
    end_date: "2021-12-31"

  - name: "Post-COVID"
    start_date: "2022-01-01"
    end_date: "2024-12-31"

  - name: "5 Year"
    start_date: "2020-01-01"
    end_date: "2024-12-31"
```

This configuration will run 16 backtests (4 tickers × 4 time periods) and
generate comparison reports showing performance across the matrix.

### Common Vanguard Tickers

- **VTI**: Total Stock Market ETF
- **VOO**: S&P 500 ETF
- **VEA**: FTSE Developed Markets ETF
- **VEU**: FTSE All-World ex-US ETF
- **BND**: Total Bond Market ETF
- **VXUS**: Total International Stock ETF

Use ETFs over mutual funds (VTSAX, VFIAX) for better yfinance compatibility.
