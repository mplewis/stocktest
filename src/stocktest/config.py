"""Configuration management for stocktest using Pydantic."""

from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator


class TimePeriod(BaseModel):
    """Named time period for backtesting."""

    name: str = Field(min_length=1)
    start_date: datetime
    end_date: datetime

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: datetime, info) -> datetime:
        """Ensure end_date > start_date."""
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class Config(BaseModel):
    """Root configuration for stocktest."""

    time_periods: list[TimePeriod] = Field(min_length=1)
    tickers: list[str] = Field(min_length=1)

    @field_validator("tickers")
    @classmethod
    def normalize_tickers(cls, v: list[str]) -> list[str]:
        """Normalize ticker symbols to uppercase."""
        return [ticker.upper().strip() for ticker in v]


def load_config(config_path: Path | str) -> Config:
    """Load and validate configuration from YAML file."""
    path = Path(config_path)
    with path.open() as f:
        data = yaml.safe_load(f)
    return Config(**data)
