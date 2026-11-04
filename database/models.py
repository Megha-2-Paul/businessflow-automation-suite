"""Core persistence models for configuration and processing provenance."""
from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
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
    dataset_sources: Mapped[list[DatasetSource]] = relationship(back_populates="business")
    processing_jobs: Mapped[list[ProcessingJob]] = relationship(back_populates="business")
    invoices: Mapped[list[Invoice]] = relationship(back_populates="business")
    orders: Mapped[list[Order]] = relationship(back_populates="business")
    products: Mapped[list[Product]] = relationship(back_populates="business")
    inventory_counts: Mapped[list[InventoryCount]] = relationship(back_populates="business")


class DatasetSource(Base):
    """Public or user-provided dataset provenance record."""

    __tablename__ = "dataset_sources"
    __table_args__ = (
        UniqueConstraint(
            "business_id", "source_name", "source_version", name="uq_dataset_source_version"
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
    imports: Mapped[list[DatasetImport]] = relationship(back_populates="dataset_source")


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

    dataset_source: Mapped[DatasetSource] = relationship(back_populates="imports")


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
    invoices: Mapped[list[Invoice]] = relationship(back_populates="processing_job")


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


class Invoice(Base):
    """A human-confirmed invoice record; original documents are not stored."""

    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint(
            "business_id", "supplier", "invoice_number", name="uq_invoice_supplier_number"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    processing_job_id: Mapped[int] = mapped_column(
        ForeignKey("processing_jobs.id", ondelete="RESTRICT"), nullable=False
    )
    supplier: Mapped[str] = mapped_column(String(200), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(120), nullable=False)
    invoice_date: Mapped[date | None] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date)
    currency: Mapped[str | None] = mapped_column(String(3))
    subtotal: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    tax: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    total: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    review_status: Mapped[str] = mapped_column(String(20), nullable=False, default="confirmed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    business: Mapped[Business] = relationship(back_populates="invoices")
    processing_job: Mapped[ProcessingJob] = relationship(back_populates="invoices")
    line_items: Mapped[list[InvoiceLineItem]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )


class InvoiceLineItem(Base):
    """A reviewed invoice line item."""

    __tablename__ = "invoice_line_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    invoice: Mapped[Invoice] = relationship(back_populates="line_items")

class Product(Base):
    """A sellable or trackable item in a business catalogue."""

    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("business_id", "sku", name="uq_product_business_sku"),
        CheckConstraint("length(sku) > 0", name="ck_product_sku_not_empty"),
        CheckConstraint("length(name) > 0", name="ck_product_name_not_empty"),
        CheckConstraint("stock_on_hand >= 0", name="ck_product_stock_nonnegative"),
        CheckConstraint("reorder_level >= 0", name="ck_product_reorder_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    sku: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default="unit")
    stock_on_hand: Mapped[Decimal] = mapped_column(
        Numeric(14, 3), nullable=False, default=Decimal("0")
    )
    reorder_level: Mapped[Decimal] = mapped_column(
        Numeric(14, 3), nullable=False, default=Decimal("0")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    business: Mapped[Business] = relationship(back_populates="products")
    movements: Mapped[list[StockMovement]] = relationship(back_populates="product")
    order_lines: Mapped[list[OrderLineItem]] = relationship(back_populates="product")


class StockMovement(Base):
    """Immutable inventory ledger entry recording a stock quantity change."""

    __tablename__ = "stock_movements"
    __table_args__ = (
        CheckConstraint("quantity_delta != 0", name="ck_stock_movement_nonzero"),
        CheckConstraint(
            "movement_type IN ('opening_balance', 'receipt', 'issue', 'adjustment', "
            "'stocktake_adjustment', 'order_fulfilment')",
            name="ck_stock_movement_type",
        ),
        UniqueConstraint("order_id", "product_id", name="uq_stock_order_product"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id", ondelete="RESTRICT")
    )
    movement_type: Mapped[str] = mapped_column(String(30), nullable=False)
    quantity_delta: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    quantity_after: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    product: Mapped[Product] = relationship(back_populates="movements")
    order: Mapped[Order | None] = relationship(back_populates="stock_movements")


class InventoryCount(Base):
    """A physical stocktake session for one business."""

    __tablename__ = "inventory_counts"
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'reconciled')", name="ck_inventory_count_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    business: Mapped[Business] = relationship(back_populates="inventory_counts")
    lines: Mapped[list[InventoryCountLine]] = relationship(
        back_populates="inventory_count", cascade="all, delete-orphan"
    )


class InventoryCountLine(Base):
    """A counted quantity and recorded balance captured during a stocktake."""

    __tablename__ = "inventory_count_lines"
    __table_args__ = (
        UniqueConstraint("inventory_count_id", "product_id", name="uq_count_product"),
        CheckConstraint("counted_quantity >= 0", name="ck_counted_quantity_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inventory_count_id: Mapped[int] = mapped_column(
        ForeignKey("inventory_counts.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    recorded_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    counted_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)

    inventory_count: Mapped[InventoryCount] = relationship(back_populates="lines")
    product: Mapped[Product] = relationship()


class Order(Base):
    """Customer order with a controlled lifecycle and calculated total."""

    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("business_id", "order_number", name="uq_order_business_number"),
        CheckConstraint(
            "status IN ('Draft', 'Confirmed', 'Processing', 'Fulfilled', 'Cancelled')",
            name="ck_order_status",
        ),
        CheckConstraint("length(order_number) > 0", name="ck_order_number_not_empty"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    order_number: Mapped[str] = mapped_column(String(120), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    customer_email: Mapped[str | None] = mapped_column(String(254))
    order_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Draft")
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    business: Mapped[Business] = relationship(back_populates="orders")
    line_items: Mapped[list[OrderLineItem]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    stock_movements: Mapped[list[StockMovement]] = relationship(back_populates="order")


class OrderLineItem(Base):
    """A product or service included in an order."""

    __tablename__ = "order_line_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT")
    )

    order: Mapped[Order] = relationship(back_populates="line_items")
    product: Mapped[Product | None] = relationship(back_populates="order_lines")
