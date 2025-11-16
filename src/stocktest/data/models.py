"""SQLAlchemy ORM models for stocktest database."""

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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
    cache_metadata: Mapped["CacheMetadata"] = relationship(
        "CacheMetadata", back_populates="security", uselist=False
    )


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


class NoDataRange(Base):
    """Tracks date ranges where no data is available for a security."""

    __tablename__ = "no_data_ranges"

    security_id: Mapped[int] = mapped_column(ForeignKey("securities.id"), primary_key=True)
    start_timestamp: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    end_timestamp: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    last_checked: Mapped[int] = mapped_column(BigInteger, nullable=False)

    security: Mapped["Security"] = relationship("Security")

    __table_args__ = (
        Index("idx_no_data_ranges_security", "security_id"),
        Index("idx_no_data_ranges_timestamps", "security_id", "start_timestamp", "end_timestamp"),
    )
