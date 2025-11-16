"""Tests for configuration management."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from stocktest.config import Config, TimePeriod, load_config


def test_loads_valid_configuration(tmp_path):
    """Loads and validates a valid configuration file."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
tickers:
  - VTI
  - VOO

time_periods:
  - name: "Test Period"
    start_date: "2020-01-01"
    end_date: "2021-01-01"
""")

    config = load_config(config_file)

    assert len(config.tickers) == 2
    assert config.tickers == ["VTI", "VOO"]
    assert len(config.time_periods) == 1
    assert config.time_periods[0].name == "Test Period"


def test_validates_invalid_date_range():
    """Rejects time periods where end_date <= start_date."""
    with pytest.raises(ValidationError) as exc_info:
        TimePeriod(
            name="Invalid",
            start_date=datetime(2021, 1, 1),
            end_date=datetime(2020, 1, 1),
        )

    assert "end_date must be after start_date" in str(exc_info.value)


def test_normalizes_tickers():
    """Normalizes ticker symbols to uppercase and strips whitespace."""
    config = Config(
        tickers=["  vti  ", "voo", "VEA"],
        time_periods=[
            TimePeriod(
                name="Test",
                start_date=datetime(2020, 1, 1),
                end_date=datetime(2021, 1, 1),
            )
        ],
    )

    assert config.tickers == ["VTI", "VOO", "VEA"]


def test_validates_empty_tickers():
    """Rejects configuration with empty tickers list."""
    with pytest.raises(ValidationError) as exc_info:
        Config(
            tickers=[],
            time_periods=[
                TimePeriod(
                    name="Test",
                    start_date=datetime(2020, 1, 1),
                    end_date=datetime(2021, 1, 1),
                )
            ],
        )

    assert "at least 1 item" in str(exc_info.value).lower()


def test_validates_empty_periods():
    """Rejects configuration with empty time periods list."""
    with pytest.raises(ValidationError) as exc_info:
        Config(tickers=["VTI"], time_periods=[])

    assert "at least 1 item" in str(exc_info.value).lower()
