"""Validation helpers for order inputs."""
from decimal import Decimal, InvalidOperation
from typing import Any


class OrderValidationError(ValueError):
    """Raised when order data is invalid."""


def money(value: Any, field: str) -> Decimal:
    """Convert a value to a finite, non-negative monetary amount."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise OrderValidationError(f"{field} must be a valid number.") from exc
    if not amount.is_finite() or amount < 0:
        raise OrderValidationError(f"{field} must be a finite, non-negative number.")
    return amount.quantize(Decimal("0.01"))


def quantity(value: Any, field: str) -> Decimal:
    """Convert a value to a finite, positive quantity."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise OrderValidationError(f"{field} must be a valid number.") from exc
    if not amount.is_finite() or amount <= 0:
        raise OrderValidationError(f"{field} must be greater than zero.")
    return amount.quantize(Decimal("0.001"))


def clean_line_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate and normalise order lines and calculate each line amount."""
    if not items:
        raise OrderValidationError("An order must contain at least one line item.")
    cleaned = []
    for index, item in enumerate(items, start=1):
        description = str(item.get("description", "")).strip()
        if not description:
            raise OrderValidationError(f"Line {index} description is required.")
        qty = quantity(item.get("quantity"), f"Line {index} quantity")
        price = money(item.get("unit_price"), f"Line {index} unit price")
        cleaned.append({
            "description": description[:500],
            "quantity": qty,
            "unit_price": price,
            "amount": (qty * price).quantize(Decimal("0.01")),
        })
    return cleaned
