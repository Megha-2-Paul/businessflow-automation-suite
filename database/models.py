"""Core persistence models for configuration and processing provenance."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class Business(Base):
    """A business workspace owning imported data and processing activity."""

    __tablename__ = "businesses"
    __table_args__ = (
        CheckConstraint("length(name) > 0", name="ck_business_name_not_empty"),
        CheckConstraint("length(currency) = 3", name="ck_business_currency_length"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    dataset_sources: Mapped[list[DatasetSource]] = relationship(
        back_populates="business"
    )
    processing_jobs: Mapped[list[ProcessingJob]] = relationship(
        back_populates="business"
    )


class DatasetSource(Base):
    """Public or user-provided dataset provenance record."""

    __tablename__ = "dataset_sources"
    __table_args__ = (
        UniqueConstraint(
            "business_id",
            "source_name",
            "source_version",
            name="uq_dataset_source_version",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    source_name: Mapped[str] = mapped_column(String(250), nullable=False)
    publisher: Mapped[str] = mapped_column(String(250), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    license_name: Mapped[str] = mapped_column(String(120), nullable=False)
    attribution: Mapped[str | None] = mapped_column(Text)
    source_version: Mapped[str] = mapped_column(
        String(100), nullable=False, default="unspecified"
    )
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    business: Mapped[Business] = relationship(back_populates="dataset_sources")
    imports: Mapped[list[DatasetImport]] = relationship(
        back_populates="dataset_source"
    )


class DatasetImport(Base):
    """An individual download or ingestion of a registered dataset source."""

    __tablename__ = "dataset_imports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_source_id: Mapped[int] = mapped_column(
        ForeignKey("dataset_sources.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    downloaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    row_count: Mapped[int | None] = mapped_column(Integer)

    dataset_source: Mapped[DatasetSource] = relationship(
        back_populates="imports"
    )


class ProcessingJob(Base):
    """One execution of an application workflow."""

    __tablename__ = "processing_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'completed_with_errors', 'failed')",
            name="ck_processing_job_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    job_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    records_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_succeeded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    business: Mapped[Business] = relationship(back_populates="processing_jobs")
    logs: Mapped[list[ProcessingLog]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    errors: Mapped[list[ProcessingError]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class ProcessingLog(Base):
    """Structured event associated with a processing job."""

    __tablename__ = "processing_logs"
    __table_args__ = (
        CheckConstraint(
            "level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR')",
            name="ck_processing_log_level",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False
    )
    level: Mapped[str] = mapped_column(String(10), nullable=False, default="INFO")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    job: Mapped[ProcessingJob] = relationship(back_populates="logs")


class ProcessingError(Base):
    """A record-level or workflow-level processing exception."""

    __tablename__ = "processing_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False
    )
    row_number: Mapped[int | None] = mapped_column(Integer)
    issue_type: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    job: Mapped[ProcessingJob] = relationship(back_populates="errors")
